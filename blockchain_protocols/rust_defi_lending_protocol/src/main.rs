//! Demo: register users, deposit collateral, borrow, accrue interest, repay,
//! then trigger a liquidation flow.

use rust_defi_lending_protocol::Protocol;

const UNIT: u128 = 1_000_000;

fn fmt(units: u128) -> String { format!("{}.{:06}", units / UNIT, units % UNIT) }

fn main() {
    let mut p = Protocol::new();
    p.register_user("alice", 1000 * UNIT);
    p.register_user("liquidator", 0);

    p.deposit_collateral("alice", 150 * UNIT).unwrap();
    let loan_id = p.borrow("alice", 100 * UNIT).unwrap();
    let loan = p.loan(loan_id).unwrap();
    println!(
        "Loan #{loan_id}: principal={} collateral={} rate={} bps",
        fmt(loan.principal), fmt(loan.collateral), loan.interest_rate_bps
    );

    // One "year" of interest.
    p.advance_time(10_000);
    let owed = p.loan(loan_id).unwrap().outstanding(p.now_tick);
    println!("After 1 year, alice owes: {}", fmt(owed));

    p.repay(loan_id).unwrap();
    let alice = p.user("alice").unwrap();
    println!(
        "After repay: alice balance={} collateral={}",
        fmt(alice.balance), fmt(alice.collateral_locked)
    );

    // Now demonstrate liquidation on a second loan that goes underwater.
    p.deposit_collateral("alice", 150 * UNIT).unwrap();
    let bad_loan = p.borrow("alice", 100 * UNIT).unwrap();
    p.advance_time(40 * 10_000); // exaggerated drift
    println!(
        "Loan #{bad_loan} outstanding now: {}",
        fmt(p.loan(bad_loan).unwrap().outstanding(p.now_tick))
    );
    p.liquidate(bad_loan, "liquidator").unwrap();
    println!(
        "After liquidation: liquidator balance = {}",
        fmt(p.user("liquidator").unwrap().balance)
    );

    println!("Ledger has {} events.", p.ledger.len());
}
