//! Append-only ledger of state-changing events. Acts as the "transparent,
//! tamper-proof record" the README refers to.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LedgerEvent {
    Register { user: String, initial_balance: u128 },
    Deposit  { user: String, amount: u128 },
    Withdraw { user: String, amount: u128 },
    Borrow {
        loan_id: u64,
        borrower: String,
        principal: u128,
        collateral: u128,
        interest_rate_bps: u32,
    },
    Repay { loan_id: u64, borrower: String, principal: u128, interest_paid: u128 },
    Liquidate {
        loan_id: u64,
        borrower: String,
        liquidator: String,
        collateral_seized: u128,
        debt_cleared: u128,
    },
}

#[derive(Debug, Default)]
pub struct Ledger {
    events: Vec<LedgerEvent>,
}

impl Ledger {
    pub fn new() -> Self { Self::default() }
    pub fn record(&mut self, event: LedgerEvent) { self.events.push(event); }
    pub fn events(&self) -> &[LedgerEvent] { &self.events }
    pub fn len(&self) -> usize { self.events.len() }
    pub fn is_empty(&self) -> bool { self.events.is_empty() }
}
