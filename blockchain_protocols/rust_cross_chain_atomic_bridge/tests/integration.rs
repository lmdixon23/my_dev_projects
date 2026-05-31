//! Integration tests: exercise end-to-end transfer flows through the
//! crate's public API only. Cargo discovers integration tests at
//! `<crate>/tests/*.rs`, so this file is what `cargo test` actually runs;
//! the copy under `src/integration.rs` is being phased out.

use std::time::Duration;

use rust_cross_chain_atomic_bridge::{
    bridge_transfer, rollback_transfer, Asset, Bridge, HoldingKind, LockState, MockChain,
};

async fn seed(bridge: &Bridge, chain_name: &str, asset_id: &str, amount: u64) {
    let h = bridge.chain(chain_name).unwrap();
    let mut chain = h.lock().await;
    let audit_arc = bridge.audit();
    let mut audit = audit_arc.lock().await;
    chain.deposit(
        Asset {
            id: asset_id.into(),
            symbol: "X".into(),
            amount,
            origin_chain: chain_name.into(),
        },
        HoldingKind::Native,
        &mut audit,
    );
}

#[tokio::test]
async fn end_to_end_transfer_conserves_value_and_wraps_correctly() {
    let mut bridge = Bridge::new();
    let _ = bridge.register(MockChain::new("ChainA"));
    let _ = bridge.register(MockChain::new("ChainB"));
    seed(&bridge, "ChainA", "x", 500).await;

    let before = bridge.total_value().await;
    bridge_transfer(
        &bridge,
        "ChainA",
        "ChainB",
        "x",
        b"reveal-me",
        Duration::from_secs(60),
        false,
    )
    .await
    .unwrap();
    let after = bridge.total_value().await;

    assert_eq!(before, after, "value not conserved: {} -> {}", before, after);
    assert!(
        bridge.chain("ChainA").unwrap().lock().await.holding("x").is_none(),
        "source-side native should be released"
    );
    let dest = bridge.chain("ChainB").unwrap();
    let dest_chain = dest.lock().await;
    let wrapped = dest_chain.holding("wx").expect("destination should hold wrapped");
    assert_eq!(wrapped.asset.amount, 500);
    match &wrapped.kind {
        HoldingKind::Wrapped { origin } => assert_eq!(origin, "ChainA"),
        other => panic!("expected wrapped, got {:?}", other),
    }
}

#[tokio::test]
async fn transfer_rollback_on_user_abort_restores_state() {
    let mut bridge = Bridge::new();
    let _ = bridge.register(MockChain::new("ChainA"));
    let _ = bridge.register(MockChain::new("ChainB"));
    seed(&bridge, "ChainA", "y", 200).await;

    let before = bridge.total_value().await;
    let lock_id = bridge_transfer(
        &bridge,
        "ChainA",
        "ChainB",
        "y",
        b"never-revealed",
        Duration::from_millis(1),
        true, // user disappears after wrap
    )
    .await
    .unwrap();

    std::thread::sleep(Duration::from_millis(10));
    rollback_transfer(&bridge, "ChainA", "ChainB", "y", lock_id)
        .await
        .unwrap();

    let after = bridge.total_value().await;
    assert_eq!(before, after, "rollback must restore total value");
    assert!(
        bridge.chain("ChainA").unwrap().lock().await.holding("y").is_some(),
        "source asset must remain available to the original owner after refund"
    );
    assert!(
        bridge.chain("ChainB").unwrap().lock().await.holding("wy").is_none(),
        "wrapped must be burned on rollback"
    );
    assert_eq!(
        bridge.chain("ChainA").unwrap().lock().await.lock_state(lock_id),
        Some(LockState::Refunded)
    );
}

#[tokio::test]
async fn two_concurrent_transfers_both_succeed() {
    let mut bridge = Bridge::new();
    let _ = bridge.register(MockChain::new("A"));
    let _ = bridge.register(MockChain::new("B"));
    seed(&bridge, "A", "a0", 10).await;
    seed(&bridge, "A", "a1", 10).await;

    let before = bridge.total_value().await;
    let (r0, r1) = tokio::join!(
        bridge_transfer(&bridge, "A", "B", "a0", b"k0", Duration::from_secs(60), false),
        bridge_transfer(&bridge, "A", "B", "a1", b"k1", Duration::from_secs(60), false),
    );
    r0.unwrap();
    r1.unwrap();
    assert_eq!(bridge.total_value().await, before);
    assert!(bridge.chain("B").unwrap().lock().await.holding("wa0").is_some());
    assert!(bridge.chain("B").unwrap().lock().await.holding("wa1").is_some());
}
