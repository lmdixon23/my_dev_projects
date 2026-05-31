use rust_defi_lending_protocol::{LedgerEvent, Protocol};

const UNIT: u128 = 1_000_000;

#[test]
fn full_lifecycle_emits_expected_ledger_events() {
    let mut p = Protocol::new();
    p.register_user("alice", 1000 * UNIT);
    p.deposit_collateral("alice", 150 * UNIT).unwrap();
    let lid = p.borrow("alice", 100 * UNIT).unwrap();
    p.advance_time(10_000);
    p.repay(lid).unwrap();

    let events = p.ledger.events();
    assert!(matches!(events[0], LedgerEvent::Register { .. }));
    assert!(matches!(events[1], LedgerEvent::Deposit { .. }));
    assert!(matches!(events[2], LedgerEvent::Borrow { .. }));
    assert!(matches!(events[3], LedgerEvent::Repay { .. }));
}

#[test]
fn cannot_repay_unknown_loan() {
    let mut p = Protocol::new();
    p.register_user("alice", 0);
    let err = p.repay(9999).unwrap_err();
    assert!(matches!(err, rust_defi_lending_protocol::LendingError::UnknownLoan(9999)));
}
