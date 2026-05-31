//! Demo binary: seeds a bridge with two chains, runs a successful
//! transfer, and prints the audit trail.

use std::time::Duration;

use rust_cross_chain_atomic_bridge::{
    bridge_transfer, Asset, Bridge, HoldingKind, MockChain,
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let mut bridge = Bridge::new();
    let ethereum = bridge.register(MockChain::new("Ethereum"));
    let _polkadot = bridge.register(MockChain::new("Polkadot"));

    // Seed Ethereum with a native asset.
    {
        let mut e = ethereum.lock().await;
        let audit_arc = bridge.audit();
        let mut a = audit_arc.lock().await;
        e.deposit(
            Asset {
                id: "eth-001".into(),
                symbol: "ETH".into(),
                amount: 10_000,
                origin_chain: "Ethereum".into(),
            },
            HoldingKind::Native,
            &mut a,
        );
    }

    println!(
        "Before transfer: total value across all chains = {}",
        bridge.total_value().await
    );

    bridge_transfer(
        &bridge,
        "Ethereum",
        "Polkadot",
        "eth-001",
        b"correct horse battery staple",
        Duration::from_secs(60),
        false,
    )
    .await?;

    println!(
        "After transfer:  total value across all chains = {}",
        bridge.total_value().await
    );
    println!("(Value is conserved at-rest: now held as wrapped wETH on Polkadot.)");

    let audit_arc = bridge.audit();
    let a = audit_arc.lock().await;
    println!("\nAudit log ({} events):", a.len());
    for (_, ev) in a.events() {
        println!("  - {:?}", ev);
    }

    Ok(())
}
