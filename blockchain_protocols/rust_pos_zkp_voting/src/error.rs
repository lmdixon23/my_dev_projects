use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ChainError {
    #[error("voter '{0}' is not registered")]
    UnregisteredVoter(String),

    #[error("voter '{0}' has already voted")]
    DoubleVote(String),

    #[error("signature verification failed for voter '{0}'")]
    BadSignature(String),

    #[error("eligibility commitment mismatch for voter '{0}'")]
    BadCommitment(String),

    #[error("no validators registered")]
    NoValidators,

    #[error("chain integrity check failed at block {0}")]
    BrokenChain(u64),
}
