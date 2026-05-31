//! Hashed Time-Lock Contracts.
//!
//! An HTLC commits to `hash(preimage)` at creation time, without storing the
//! preimage alongside it. The preimage is supplied at claim time, the
//! verifier re-hashes it, and the comparison is constant-time. This is the
//! standard primitive underlying atomic swaps and bridge protocols.

use std::time::{Duration, SystemTime};

use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;

use crate::error::BridgeError;

#[derive(Debug, Clone)]
pub struct Htlc {
    hash: [u8; 32],
    timeout: SystemTime,
}

impl Htlc {
    /// Create a new HTLC committing to `hash(preimage)`, expiring after
    /// `duration` from now.
    pub fn commit(preimage: &[u8], duration: Duration) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(preimage);
        let hash: [u8; 32] = hasher.finalize().into();
        Self { hash, timeout: SystemTime::now() + duration }
    }

    /// Reconstruct an HTLC from its components (e.g., after deserialization
    /// or when re-deriving from on-chain state). Note this does not verify
    /// the hash is correct for any preimage; it just packages the fields.
    pub fn from_parts(hash: [u8; 32], timeout: SystemTime) -> Self {
        Self { hash, timeout }
    }

    pub fn hash(&self) -> [u8; 32] { self.hash }
    pub fn timeout(&self) -> SystemTime { self.timeout }

    /// Verify that `preimage` hashes to the committed value and the
    /// contract has not expired. Comparison is constant-time.
    pub fn verify(&self, preimage: &[u8]) -> Result<(), BridgeError> {
        if SystemTime::now() > self.timeout {
            return Err(BridgeError::Expired(self.timeout));
        }
        let mut hasher = Sha256::new();
        hasher.update(preimage);
        let provided: [u8; 32] = hasher.finalize().into();
        if provided.ct_eq(&self.hash).into() {
            Ok(())
        } else {
            Err(BridgeError::InvalidPreimage)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_correct_preimage() {
        let h = Htlc::commit(b"alpha", Duration::from_secs(60));
        assert!(h.verify(b"alpha").is_ok());
    }

    #[test]
    fn rejects_wrong_preimage() {
        let h = Htlc::commit(b"alpha", Duration::from_secs(60));
        assert!(matches!(h.verify(b"beta"), Err(BridgeError::InvalidPreimage)));
    }

    #[test]
    fn rejects_after_expiry() {
        let h = Htlc::commit(b"alpha", Duration::from_millis(1));
        std::thread::sleep(Duration::from_millis(10));
        assert!(matches!(h.verify(b"alpha"), Err(BridgeError::Expired(_))));
    }
}
