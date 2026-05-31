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

    #[error("no authorities registered")]
    NoAuthorities,

    /// The signing key offered to `mine_block` does not belong to the
    /// authority whose round-robin turn it is.
    #[error("wrong proposer: it is '{expected}'s turn, not '{got}'")]
    WrongProposer { expected: String, got: String },

    #[error("proposer signature verification failed at block {0}")]
    BadProposerSignature(u64),

    #[error("chain integrity check failed at block {0}")]
    BrokenChain(u64),
}
