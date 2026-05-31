//! Bridge: holds registered chains, orchestrates cross-chain transfers,
//! and exposes a rollback path for aborted transfers.
//!
//! In a real system the protocol roles (user, relayer, source-chain
//! contract, destination-chain contract) live in distinct trust domains
//! and communicate via observable on-chain events. Here all roles live
//! in one process; cross-chain message boundaries are marked by explicit
//! `MessageSent` / `MessageReceived` audit events so the architecture is
//! honest about where the simulation ends.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

use log::info;
use tokio::sync::Mutex;
use uuid::Uuid;

use crate::audit::{AuditEvent, AuditLog};
use crate::chain::{Asset, HoldingKind, MockChain};
use crate::error::BridgeError;
use crate::htlc::Htlc;

pub struct Bridge {
    chains: HashMap<String, Arc<Mutex<MockChain>>>,
    audit: Arc<Mutex<AuditLog>>,
}

impl Bridge {
    pub fn new() -> Self {
        Self {
            chains: HashMap::new(),
            audit: Arc::new(Mutex::new(AuditLog::default())),
        }
    }

    pub fn register(&mut self, chain: MockChain) -> Arc<Mutex<MockChain>> {
        let name = chain.name().to_string();
        let handle = Arc::new(Mutex::new(chain));
        self.chains.insert(name, handle.clone());
        handle
    }

    pub fn chain(&self, name: &str) -> Result<Arc<Mutex<MockChain>>, BridgeError> {
        self.chains
            .get(name)
            .cloned()
            .ok_or_else(|| BridgeError::UnknownChain(name.to_string()))
    }

    pub fn audit(&self) -> Arc<Mutex<AuditLog>> { self.audit.clone() }

    /// Sum of holdings across all registered chains.
    pub async fn total_value(&self) -> u64 {
        let mut sum = 0;
        for h in self.chains.values() {
            sum += h.lock().await.total_balance();
        }
        sum
    }
}

impl Default for Bridge {
    fn default() -> Self { Self::new() }
}

/// Transfer `asset_id` from `source_name` to `dest_name`.
///
/// Protocol order:
///   1. Lock the asset on the source chain under `hash(preimage)` with
///      timeout `lock_duration`.
///   2. Send `LockObserved` to the destination chain.
///   3. Destination mints a wrapped representation of the asset.
///   4. (Implicit in this single-process simulation) the user claims the
///      wrapped asset on the destination.
///   5. Send `PreimageRevealed` to the source chain.
///   6. Source verifies the preimage against the lock's commitment and
///      releases the asset.
///
/// If `simulate_user_disappears` is true, the function exits after step 3
/// without revealing the preimage. The returned `Uuid` is the source-chain
/// lock id; pass it to [`rollback_transfer`] to unwind once the timeout
/// has passed.
pub async fn bridge_transfer(
    bridge: &Bridge,
    source_name: &str,
    dest_name: &str,
    asset_id: &str,
    preimage: &[u8],
    lock_duration: Duration,
    simulate_user_disappears: bool,
) -> Result<Uuid, BridgeError> {
    let source = bridge.chain(source_name)?;
    let dest = bridge.chain(dest_name)?;
    let audit = bridge.audit();

    let htlc = Htlc::commit(preimage, lock_duration);

    // 1. Lock on source.
    let (lock_id, asset_snapshot) = {
        let mut s = source.lock().await;
        let mut a = audit.lock().await;
        let id = s.lock(asset_id, &htlc, &mut a)?;
        let snap = s.holding(asset_id).unwrap().asset.clone();
        (id, snap)
    };

    // 2. Cross-chain message: source -> dest.
    audit.lock().await.record(AuditEvent::MessageSent {
        from: source_name.to_string(),
        to: dest_name.to_string(),
        kind: "LockObserved",
    });

    // 3. Destination mints the wrapped representation.
    {
        let mut d = dest.lock().await;
        let mut a = audit.lock().await;
        a.record(AuditEvent::MessageReceived {
            at: dest_name.to_string(),
            kind: "LockObserved",
        });
        let wrapped = Asset {
            id: format!("w{}", asset_snapshot.id),
            symbol: format!("w{}", asset_snapshot.symbol),
            amount: asset_snapshot.amount,
            origin_chain: source_name.to_string(),
        };
        d.deposit(
            wrapped,
            HoldingKind::Wrapped { origin: source_name.to_string() },
            &mut a,
        );
    }

    if simulate_user_disappears {
        info!(
            "bridge_transfer({} -> {}): user aborted after wrap; lock_id={} returned for rollback",
            source_name, dest_name, lock_id
        );
        return Ok(lock_id);
    }

    // 5. Cross-chain message: dest -> source.
    audit.lock().await.record(AuditEvent::MessageSent {
        from: dest_name.to_string(),
        to: source_name.to_string(),
        kind: "PreimageRevealed",
    });

    // 6. Source release using the revealed preimage.
    {
        let mut s = source.lock().await;
        let mut a = audit.lock().await;
        a.record(AuditEvent::MessageReceived {
            at: source_name.to_string(),
            kind: "PreimageRevealed",
        });
        s.release(lock_id, preimage, &mut a)?;
    }

    info!("bridge_transfer({} -> {}): success", source_name, dest_name);
    Ok(lock_id)
}

/// Unwind an aborted transfer: burn the wrapped representation on the
/// destination and refund the source-chain lock. The source-chain timeout
/// must have passed.
pub async fn rollback_transfer(
    bridge: &Bridge,
    source_name: &str,
    dest_name: &str,
    asset_id: &str,
    lock_id: Uuid,
) -> Result<(), BridgeError> {
    let source = bridge.chain(source_name)?;
    let dest = bridge.chain(dest_name)?;
    let audit = bridge.audit();

    {
        let mut d = dest.lock().await;
        let mut a = audit.lock().await;
        d.burn_wrapped(&format!("w{}", asset_id), &mut a)?;
    }
    {
        let mut s = source.lock().await;
        let mut a = audit.lock().await;
        s.refund(lock_id, &mut a)?;
    }
    Ok(())
}
