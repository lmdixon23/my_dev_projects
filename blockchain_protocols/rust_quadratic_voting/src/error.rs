use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum QvError {
    #[error("voter '{0}' is not registered")]
    UnregisteredVoter(String),

    #[error("voter '{voter}' has insufficient credits (have {have}, need {need})")]
    InsufficientCredits { voter: String, have: u64, need: u64 },

    #[error("voter '{0}' has delegated and cannot cast votes directly")]
    HasDelegated(String),

    #[error("delegation from '{from}' to '{to}' would create a cycle")]
    DelegationCycle { from: String, to: String },

    #[error("voter '{0}' has already delegated")]
    AlreadyDelegated(String),

    #[error("vote count must be > 0")]
    ZeroVotes,
}

impl QvError {
    pub fn unregistered(v: &str) -> Self { Self::UnregisteredVoter(v.to_string()) }
}
