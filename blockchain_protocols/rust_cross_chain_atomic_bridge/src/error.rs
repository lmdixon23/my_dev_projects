//! Error types for the bridge simulation.

use std::time::SystemTime;

use thiserror::Error;
use uuid::Uuid;

#[derive(Debug, Error)]
pub enum BridgeError {
    #[error("asset {asset} not found on chain {chain}")]
    AssetNotFound { asset: String, chain: String },

    #[error("lock {0} not found")]
    LockNotFound(Uuid),

    #[error("HTLC expired (timeout was {0:?})")]
    Expired(SystemTime),

    #[error("lock has not yet expired (timeout {0:?})")]
    NotYetExpired(SystemTime),

    #[error("invalid preimage")]
    InvalidPreimage,

    #[error("lock already settled")]
    AlreadySettled,

    #[error("chain {0} not registered with the bridge")]
    UnknownChain(String),
}
