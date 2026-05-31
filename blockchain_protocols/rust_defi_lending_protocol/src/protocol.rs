//! Lending protocol core: users, loans, dynamic rate, liquidation.

use std::collections::HashMap;

use crate::error::LendingError;
use crate::ledger::{Ledger, LedgerEvent};

const BPS_DENOM: u128 = 10_000;
/// 150 % collateralization required to open a loan.
const INITIAL_COLLATERAL_RATIO_BPS: u128 = 15_000;
/// Below 120 % the loan can be liquidated.
const LIQUIDATION_THRESHOLD_BPS: u128 = 12_000;
/// Base rate when utilization = 0 (annualized in basis points, 200 = 2 %).
const BASE_RATE_BPS: u128 = 200;
/// Slope * utilization_bps contribution. e.g. 100 % utilization adds 2000 bps.
const RATE_SLOPE_BPS_PER_BPS: u128 = 2000;

#[derive(Debug, Clone)]
pub struct User {
    pub id: String,
    pub balance: u128,
    pub collateral_locked: u128,
}

#[derive(Debug, Clone)]
pub struct Loan {
    pub id: u64,
    pub borrower: String,
    pub principal: u128,
    pub collateral: u128,
    pub interest_rate_bps: u32, // annualized, recorded at borrow time
    pub opened_at_tick: u64,
    pub repaid: bool,
    pub liquidated: bool,
}

impl Loan {
    /// Simple-interest accrued over `now_tick - opened_at_tick`, where
    /// `BPS_DENOM` ticks == one year. Avoids the float-rounding issues
    /// of the previous compounding-by-application logic.
    pub fn accrued_interest(&self, now_tick: u64) -> u128 {
        if self.repaid || self.liquidated || now_tick <= self.opened_at_tick {
            return 0;
        }
        let elapsed = (now_tick - self.opened_at_tick) as u128;
        self.principal * self.interest_rate_bps as u128 * elapsed / (BPS_DENOM * BPS_DENOM)
    }
    pub fn outstanding(&self, now_tick: u64) -> u128 {
        self.principal + self.accrued_interest(now_tick)
    }
}

#[derive(Debug)]
pub struct Protocol {
    pub users: HashMap<String, User>,
    pub loans: HashMap<u64, Loan>,
    pub ledger: Ledger,
    pub total_supplied: u128,
    pub total_borrowed: u128,
    pub now_tick: u64,
    next_loan_id: u64,
}

impl Default for Protocol {
    fn default() -> Self {
        Self {
            users: HashMap::new(),
            loans: HashMap::new(),
            ledger: Ledger::new(),
            total_supplied: 0,
            total_borrowed: 0,
            now_tick: 0,
            next_loan_id: 1,
        }
    }
}

impl Protocol {
    pub fn new() -> Self { Self::default() }

    pub fn advance_time(&mut self, ticks: u64) { self.now_tick += ticks; }

    /// Annualized interest rate in basis points, recomputed from utilization.
    pub fn current_rate_bps(&self) -> u32 {
        if self.total_supplied == 0 { return BASE_RATE_BPS as u32; }
        let utilization_bps = self.total_borrowed * BPS_DENOM / self.total_supplied;
        let rate = BASE_RATE_BPS + RATE_SLOPE_BPS_PER_BPS * utilization_bps / BPS_DENOM;
        rate.min(u32::MAX as u128) as u32
    }

    pub fn register_user(&mut self, id: impl Into<String>, initial_balance: u128) {
        let id = id.into();
        self.users.insert(
            id.clone(),
            User { id: id.clone(), balance: initial_balance, collateral_locked: 0 },
        );
        self.total_supplied = self.total_supplied.saturating_add(initial_balance);
        self.ledger.record(LedgerEvent::Register { user: id, initial_balance });
    }

    pub fn deposit_collateral(
        &mut self,
        user_id: &str,
        amount: u128,
    ) -> Result<(), LendingError> {
        let u = self
            .users
            .get_mut(user_id)
            .ok_or_else(|| LendingError::UnknownUser(user_id.into()))?;
        if u.balance < amount {
            return Err(LendingError::InsufficientBalance {
                user: user_id.into(),
                have: u.balance,
                need: amount,
            });
        }
        u.balance -= amount;
        u.collateral_locked += amount;
        self.ledger.record(LedgerEvent::Deposit { user: user_id.into(), amount });
        Ok(())
    }

    pub fn withdraw_collateral(
        &mut self,
        user_id: &str,
        amount: u128,
    ) -> Result<(), LendingError> {
        let u = self
            .users
            .get_mut(user_id)
            .ok_or_else(|| LendingError::UnknownUser(user_id.into()))?;
        if u.collateral_locked < amount {
            return Err(LendingError::InsufficientCollateral {
                user: user_id.into(),
                have: u.collateral_locked,
                need: amount,
            });
        }
        u.collateral_locked -= amount;
        u.balance += amount;
        self.ledger.record(LedgerEvent::Withdraw { user: user_id.into(), amount });
        Ok(())
    }

    /// Open a loan. Requires `INITIAL_COLLATERAL_RATIO_BPS` of collateral.
    pub fn borrow(
        &mut self,
        user_id: &str,
        principal: u128,
    ) -> Result<u64, LendingError> {
        let required = principal * INITIAL_COLLATERAL_RATIO_BPS / BPS_DENOM;
        // Compute the rate BEFORE taking a mutable borrow of `self.users`,
        // since current_rate_bps() needs an immutable borrow of `self`.
        let rate = self.current_rate_bps();
        let u = self
            .users
            .get_mut(user_id)
            .ok_or_else(|| LendingError::UnknownUser(user_id.into()))?;
        if u.collateral_locked < required {
            return Err(LendingError::InsufficientCollateral {
                user: user_id.into(),
                have: u.collateral_locked,
                need: required,
            });
        }
        let loan_id = self.next_loan_id;
        self.next_loan_id += 1;

        u.collateral_locked -= required;
        u.balance += principal;
        self.loans.insert(
            loan_id,
            Loan {
                id: loan_id,
                borrower: user_id.into(),
                principal,
                collateral: required,
                interest_rate_bps: rate,
                opened_at_tick: self.now_tick,
                repaid: false,
                liquidated: false,
            },
        );
        self.total_borrowed += principal;
        self.ledger.record(LedgerEvent::Borrow {
            loan_id, borrower: user_id.into(), principal, collateral: required, interest_rate_bps: rate,
        });
        Ok(loan_id)
    }

    pub fn repay(&mut self, loan_id: u64) -> Result<(), LendingError> {
        let now = self.now_tick;
        let loan = self
            .loans
            .get_mut(&loan_id)
            .filter(|l| !l.repaid && !l.liquidated)
            .ok_or(LendingError::UnknownLoan(loan_id))?;
        let owed = loan.outstanding(now);
        let interest = owed - loan.principal;
        let borrower_id = loan.borrower.clone();
        let principal = loan.principal;
        let collateral = loan.collateral;

        let u = self
            .users
            .get_mut(&borrower_id)
            .ok_or_else(|| LendingError::UnknownUser(borrower_id.clone()))?;
        if u.balance < owed {
            return Err(LendingError::InsufficientBalance {
                user: borrower_id,
                have: u.balance,
                need: owed,
            });
        }
        u.balance -= owed;
        u.collateral_locked += collateral;
        let loan = self.loans.get_mut(&loan_id).unwrap();
        loan.repaid = true;
        self.total_borrowed = self.total_borrowed.saturating_sub(principal);
        self.ledger.record(LedgerEvent::Repay {
            loan_id, borrower: borrower_id, principal, interest_paid: interest,
        });
        Ok(())
    }

    /// Anyone can liquidate a loan whose outstanding > collateral_value *
    /// LIQUIDATION_THRESHOLD_BPS / BPS_DENOM. The liquidator receives the
    /// collateral. (Real protocols pay a discount; omitted here for simplicity.)
    pub fn liquidate(
        &mut self,
        loan_id: u64,
        liquidator_id: &str,
    ) -> Result<(), LendingError> {
        let now = self.now_tick;
        let loan = self
            .loans
            .get(&loan_id)
            .filter(|l| !l.repaid && !l.liquidated)
            .ok_or(LendingError::UnknownLoan(loan_id))?
            .clone();
        let outstanding = loan.outstanding(now);
        let threshold = loan.collateral * LIQUIDATION_THRESHOLD_BPS / BPS_DENOM;
        if outstanding <= threshold {
            return Err(LendingError::NotLiquidatable(loan_id));
        }
        let liquidator = self
            .users
            .get_mut(liquidator_id)
            .ok_or_else(|| LendingError::UnknownUser(liquidator_id.into()))?;
        liquidator.balance += loan.collateral;

        let loan_mut = self.loans.get_mut(&loan_id).unwrap();
        loan_mut.liquidated = true;
        self.total_borrowed = self.total_borrowed.saturating_sub(loan.principal);
        self.ledger.record(LedgerEvent::Liquidate {
            loan_id,
            borrower: loan.borrower.clone(),
            liquidator: liquidator_id.into(),
            collateral_seized: loan.collateral,
            debt_cleared: outstanding,
        });
        Ok(())
    }

    pub fn user(&self, id: &str) -> Option<&User> { self.users.get(id) }
    pub fn loan(&self, id: u64) -> Option<&Loan> { self.loans.get(&id) }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn one() -> u128 { 1_000_000 } // one whole "unit" in micro-units

    #[test]
    fn borrow_requires_150_percent_collateral() {
        let mut p = Protocol::new();
        p.register_user("alice", 1000 * one());
        p.deposit_collateral("alice", 150 * one()).unwrap();
        // Borrow 100 -> needs exactly 150 collateral.
        let lid = p.borrow("alice", 100 * one()).unwrap();
        assert_eq!(p.user("alice").unwrap().collateral_locked, 0);
        // Now try to borrow another 1 with no remaining collateral -> rejected.
        let err = p.borrow("alice", 1 * one()).unwrap_err();
        assert!(matches!(err, LendingError::InsufficientCollateral { .. }));
        assert!(p.loan(lid).is_some());
    }

    #[test]
    fn interest_accrues_over_time_and_repayment_returns_collateral() {
        let mut p = Protocol::new();
        p.register_user("alice", 1000 * one());
        p.deposit_collateral("alice", 150 * one()).unwrap();
        let lid = p.borrow("alice", 100 * one()).unwrap();
        let rate = p.loan(lid).unwrap().interest_rate_bps as u128;

        p.advance_time(BPS_DENOM as u64); // one "year"
        let owed = p.loan(lid).unwrap().outstanding(p.now_tick);
        assert_eq!(owed, 100 * one() + 100 * one() * rate / BPS_DENOM);

        p.repay(lid).unwrap();
        let u = p.user("alice").unwrap();
        assert_eq!(u.collateral_locked, 150 * one());
        assert!(p.loan(lid).unwrap().repaid);
    }

    #[test]
    fn liquidation_seizes_collateral_when_debt_exceeds_threshold() {
        let mut p = Protocol::new();
        p.register_user("alice", 1000 * one());
        p.register_user("liq", 0);
        p.deposit_collateral("alice", 150 * one()).unwrap();
        let lid = p.borrow("alice", 100 * one()).unwrap();

        // Wait long enough that interest pushes outstanding past the 120 %
        // threshold (collateral * 1.20 = 180 units).
        p.advance_time(40 * BPS_DENOM as u64); // 40 "years" — exaggerated for the test
        let outstanding = p.loan(lid).unwrap().outstanding(p.now_tick);
        let threshold = 150 * one() * LIQUIDATION_THRESHOLD_BPS / BPS_DENOM;
        assert!(outstanding > threshold);

        p.liquidate(lid, "liq").unwrap();
        assert!(p.loan(lid).unwrap().liquidated);
        assert_eq!(p.user("liq").unwrap().balance, 150 * one());
    }

    #[test]
    fn cannot_liquidate_healthy_loan() {
        let mut p = Protocol::new();
        p.register_user("alice", 1000 * one());
        p.register_user("liq", 0);
        p.deposit_collateral("alice", 150 * one()).unwrap();
        let lid = p.borrow("alice", 100 * one()).unwrap();
        let err = p.liquidate(lid, "liq").unwrap_err();
        assert!(matches!(err, LendingError::NotLiquidatable(_)));
    }

    #[test]
    fn dynamic_rate_rises_with_utilization() {
        let mut p = Protocol::new();
        p.register_user("alice", 1000 * one());
        p.register_user("bob", 0);
        p.deposit_collateral("alice", 150 * one()).unwrap();
        let r0 = p.current_rate_bps();
        let _ = p.borrow("alice", 100 * one()).unwrap();
        let r1 = p.current_rate_bps();
        assert!(r1 > r0, "rate should rise when total_borrowed increases");
    }
}
