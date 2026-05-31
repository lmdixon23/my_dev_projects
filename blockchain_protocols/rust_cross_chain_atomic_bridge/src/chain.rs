//! Domain types for assets and chain state, plus the in-process
//! `MockChain` that holds them.

use std::collections::HashMap;
use std::time::SystemTime;

use uuid::Uuid;

use crate::audit::{AuditEvent, AuditLog};
use crate::error::BridgeError;
use crate::htlc::Htlc;

/// A unit of value. Integer base units (`u64`) — never floats for value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Asset {
    pub id: String,
    pub symbol: String,
    pub amount: u64,
    pub origin_chain: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HoldingKind {
    Native,
    Wrapped { origin: String },
}

#[derive(Debug, Clone)]
pub struct Holding {
    pub asset: Asset,
    pub kind: HoldingKind,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LockState {
    Pending,
    Claimed,
    Refunded,
}

#[derive(Debug, Clone)]
pub struct Lock {
    pub id: Uuid,
    pub asset_id: String,
    pub hash: [u8; 32],
    pub timeout: SystemTime,
    pub state: LockState,
}

#[derive(Debug)]
pub struct MockChain {
    name: String,
    holdings: HashMap<String, Holding>,
    locks: HashMap<Uuid, Lock>,
}

impl MockChain {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            holdings: HashMap::new(),
            locks: HashMap::new(),
        }
    }

    pub fn name(&self) -> &str { &self.name }

    pub fn deposit(&mut self, asset: Asset, kind: HoldingKind, audit: &mut AuditLog) {
        let id = asset.id.clone();
        let amount = asset.amount;
        match &kind {
            HoldingKind::Native => audit.record(AuditEvent::AssetMinted {
                chain: self.name.clone(),
                asset_id: id.clone(),
                amount,
            }),
            HoldingKind::Wrapped { origin } => audit.record(AuditEvent::WrappedMinted {
                chain: self.name.clone(),
                asset_id: id.clone(),
                origin: origin.clone(),
                amount,
            }),
        }
        self.holdings.insert(id, Holding { asset, kind });
    }

    pub fn holding(&self, id: &str) -> Option<&Holding> { self.holdings.get(id) }

    pub fn lock_state(&self, lock_id: Uuid) -> Option<LockState> {
        self.locks.get(&lock_id).map(|l| l.state.clone())
    }

    /// Total holdings on this chain, summed over both native and wrapped.
    pub fn total_balance(&self) -> u64 {
        self.holdings.values().map(|h| h.asset.amount).sum()
    }

    /// Place an asset under an HTLC. The asset remains in holdings until
    /// the lock is settled (released or refunded).
    pub fn lock(
        &mut self,
        asset_id: &str,
        htlc: &Htlc,
        audit: &mut AuditLog,
    ) -> Result<Uuid, BridgeError> {
        if !self.holdings.contains_key(asset_id) {
            return Err(BridgeError::AssetNotFound {
                asset: asset_id.to_string(),
                chain: self.name.clone(),
            });
        }
        let lock_id = Uuid::new_v4();
        audit.record(AuditEvent::AssetLocked {
            chain: self.name.clone(),
            lock_id,
            asset_id: asset_id.to_string(),
            hash: hex::encode(htlc.hash()),
        });
        self.locks.insert(
            lock_id,
            Lock {
                id: lock_id,
                asset_id: asset_id.to_string(),
                hash: htlc.hash(),
                timeout: htlc.timeout(),
                state: LockState::Pending,
            },
        );
        Ok(lock_id)
    }

    /// Release a locked asset given a valid preimage. Removes the asset
    /// from this chain's holdings — control passes to whomever held the
    /// preimage (in a real bridge, the bridge operator).
    pub fn release(
        &mut self,
        lock_id: Uuid,
        preimage: &[u8],
        audit: &mut AuditLog,
    ) -> Result<Asset, BridgeError> {
        let lock = self.locks.get_mut(&lock_id).ok_or(BridgeError::LockNotFound(lock_id))?;
        if !matches!(lock.state, LockState::Pending) {
            return Err(BridgeError::AlreadySettled);
        }
        let htlc = Htlc::from_parts(lock.hash, lock.timeout);
        htlc.verify(preimage)?;
        let asset = self
            .holdings
            .remove(&lock.asset_id)
            .ok_or_else(|| BridgeError::AssetNotFound {
                asset: lock.asset_id.clone(),
                chain: self.name.clone(),
            })?
            .asset;
        lock.state = LockState::Claimed;
        audit.record(AuditEvent::AssetReleased {
            chain: self.name.clone(),
            lock_id,
            asset_id: asset.id.clone(),
        });
        Ok(asset)
    }

    /// Refund after timeout: closes the lock and leaves the asset in place,
    /// returning effective control to the original owner.
    pub fn refund(&mut self, lock_id: Uuid, audit: &mut AuditLog) -> Result<(), BridgeError> {
        let lock = self.locks.get_mut(&lock_id).ok_or(BridgeError::LockNotFound(lock_id))?;
        if !matches!(lock.state, LockState::Pending) {
            return Err(BridgeError::AlreadySettled);
        }
        if SystemTime::now() <= lock.timeout {
            return Err(BridgeError::NotYetExpired(lock.timeout));
        }
        lock.state = LockState::Refunded;
        audit.record(AuditEvent::AssetRefunded {
            chain: self.name.clone(),
            lock_id,
            asset_id: lock.asset_id.clone(),
        });
        Ok(())
    }

    /// Burn a wrapped asset (e.g., as part of a rollback or reverse-
    /// direction transfer).
    pub fn burn_wrapped(
        &mut self,
        asset_id: &str,
        audit: &mut AuditLog,
    ) -> Result<Asset, BridgeError> {
        let h = self.holdings.remove(asset_id).ok_or_else(|| BridgeError::AssetNotFound {
            asset: asset_id.to_string(),
            chain: self.name.clone(),
        })?;
        audit.record(AuditEvent::WrappedBurned {
            chain: self.name.clone(),
            asset_id: asset_id.to_string(),
        });
        Ok(h.asset)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    fn fresh() -> (MockChain, AuditLog) {
        let mut chain = MockChain::new("A");
        let mut audit = AuditLog::default();
        chain.deposit(
            Asset {
                id: "asset-1".into(),
                symbol: "X".into(),
                amount: 100,
                origin_chain: "A".into(),
            },
            HoldingKind::Native,
            &mut audit,
        );
        (chain, audit)
    }

    #[test]
    fn release_requires_correct_preimage() {
        let (mut chain, mut audit) = fresh();
        let htlc = Htlc::commit(b"open", Duration::from_secs(60));
        let lock_id = chain.lock("asset-1", &htlc, &mut audit).unwrap();
        assert!(matches!(
            chain.release(lock_id, b"wrong", &mut audit),
            Err(BridgeError::InvalidPreimage)
        ));
        assert!(chain.holding("asset-1").is_some());
        assert_eq!(chain.lock_state(lock_id), Some(LockState::Pending));
    }

    #[test]
    fn refund_requires_expiry() {
        let (mut chain, mut audit) = fresh();
        let htlc = Htlc::commit(b"open", Duration::from_secs(60));
        let lock_id = chain.lock("asset-1", &htlc, &mut audit).unwrap();
        assert!(matches!(
            chain.refund(lock_id, &mut audit),
            Err(BridgeError::NotYetExpired(_))
        ));
    }

    #[test]
    fn refund_succeeds_after_expiry() {
        let (mut chain, mut audit) = fresh();
        let htlc = Htlc::commit(b"open", Duration::from_millis(1));
        let lock_id = chain.lock("asset-1", &htlc, &mut audit).unwrap();
        std::thread::sleep(Duration::from_millis(10));
        chain.refund(lock_id, &mut audit).unwrap();
        assert_eq!(chain.lock_state(lock_id), Some(LockState::Refunded));
    }
}
