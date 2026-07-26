//! Property-based conservation tests for randomized, settled bridge operations.
//!
//! The bridge may temporarily contain both a locked native holding and a newly
//! minted wrapped holding while an aborted transfer is pending. The public
//! invariant is therefore checked after every operation reaches an at-rest
//! state: either successful completion or explicit rollback.

use std::collections::HashMap;
use std::time::Duration;

use proptest::prelude::*;
use rust_cross_chain_atomic_bridge::{
    bridge_transfer, rollback_transfer, Asset, Bridge, HoldingKind, MockChain,
};

#[derive(Clone, Debug)]
struct Operation {
    asset_slot: usize,
    destination_slot: usize,
    rollback: bool,
}

fn operation_strategy(
    asset_count: usize,
    chain_count: usize,
) -> impl Strategy<Value = Vec<Operation>> {
    prop::collection::vec(
        (0usize..asset_count, 0usize..chain_count, any::<bool>()).prop_map(
            |(asset_slot, destination_slot, rollback)| Operation {
                asset_slot,
                destination_slot,
                rollback,
            },
        ),
        1..16,
    )
}

async fn seed(bridge: &Bridge, chain_name: &str, asset_id: &str, amount: u64) {
    let handle = bridge.chain(chain_name).expect("seed chain must exist");
    let mut chain = handle.lock().await;
    let audit_handle = bridge.audit();
    let mut audit = audit_handle.lock().await;

    chain.deposit(
        Asset {
            id: asset_id.to_string(),
            symbol: format!("X{asset_id}"),
            amount,
            origin_chain: chain_name.to_string(),
        },
        HoldingKind::Native,
        &mut audit,
    );
}

proptest! {
    #![proptest_config(ProptestConfig {
        cases: 64,
        max_shrink_iters: 2_048,
        .. ProptestConfig::default()
    })]

    #[test]
    fn total_value_is_conserved_across_randomized_settled_sequences(
        operations in operation_strategy(5, 3),
    ) {
        let runtime = tokio::runtime::Runtime::new()
            .expect("Tokio runtime must initialize");

        runtime.block_on(async move {
            const CHAINS: [&str; 3] = ["A", "B", "C"];
            const AMOUNTS: [u64; 5] = [3, 11, 29, 47, 101];

            let mut bridge = Bridge::new();

            for chain_name in CHAINS {
                bridge.register(MockChain::new(chain_name));
            }

            let mut locations: HashMap<usize, (String, String)> =
                HashMap::new();

            for (slot, amount) in AMOUNTS.into_iter().enumerate() {
                let chain_name = CHAINS[slot % CHAINS.len()];
                let asset_id = format!("asset-{slot}");

                seed(
                    &bridge,
                    chain_name,
                    &asset_id,
                    amount,
                )
                .await;

                locations.insert(
                    slot,
                    (
                        chain_name.to_string(),
                        asset_id,
                    ),
                );
            }

            let expected_total: u64 = AMOUNTS.into_iter().sum();

            prop_assert_eq!(
                bridge.total_value().await,
                expected_total,
                "seeded bridge total must match the model",
            );

            for (step, operation) in operations.iter().enumerate() {
                let (source_name, asset_id) = locations
                    .get(&operation.asset_slot)
                    .expect("generated asset slot must exist")
                    .clone();

                let mut destination_name =
                    CHAINS[operation.destination_slot].to_string();

                if destination_name == source_name {
                    let source_index = CHAINS
                        .iter()
                        .position(|name| *name == source_name)
                        .expect("modeled source chain must exist");

                    destination_name = CHAINS[
                        (source_index + 1) % CHAINS.len()
                    ]
                    .to_string();
                }

                let preimage = format!(
                    "slot-{}-step-{}",
                    operation.asset_slot,
                    step,
                );

                let lock_id = bridge_transfer(
                    &bridge,
                    &source_name,
                    &destination_name,
                    &asset_id,
                    preimage.as_bytes(),
                    if operation.rollback {
                        Duration::ZERO
                    } else {
                        Duration::from_secs(60)
                    },
                    operation.rollback,
                )
                .await
                .expect("generated transfer should be valid");

                if operation.rollback {
                    tokio::time::sleep(
                        Duration::from_millis(1),
                    )
                    .await;

                    rollback_transfer(
                        &bridge,
                        &source_name,
                        &destination_name,
                        &asset_id,
                        lock_id,
                    )
                    .await
                    .expect("expired aborted transfer should roll back");

                    prop_assert!(
                        bridge
                            .chain(&source_name)
                            .expect("source chain must exist")
                            .lock()
                            .await
                            .holding(&asset_id)
                            .is_some(),
                        "rollback must retain the modeled source holding",
                    );

                    prop_assert!(
                        bridge
                            .chain(&destination_name)
                            .expect("destination chain must exist")
                            .lock()
                            .await
                            .holding(&format!("w{asset_id}"))
                            .is_none(),
                        "rollback must remove the temporary wrapper",
                    );
                } else {
                    let wrapped_id = format!("w{asset_id}");

                    prop_assert!(
                        bridge
                            .chain(&source_name)
                            .expect("source chain must exist")
                            .lock()
                            .await
                            .holding(&asset_id)
                            .is_none(),
                        "successful transfer must release the source holding",
                    );

                    prop_assert!(
                        bridge
                            .chain(&destination_name)
                            .expect("destination chain must exist")
                            .lock()
                            .await
                            .holding(&wrapped_id)
                            .is_some(),
                        "successful transfer must create the modeled wrapper",
                    );

                    locations.insert(
                        operation.asset_slot,
                        (
                            destination_name.clone(),
                            wrapped_id,
                        ),
                    );
                }

                prop_assert_eq!(
                    bridge.total_value().await,
                    expected_total,
                    "total value changed after settled operation {}: {:?}",
                    step,
                    operation,
                );
            }

            Ok(())
        })?;
    }
}
