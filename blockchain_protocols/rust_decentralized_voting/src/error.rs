use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum VotingError {
    #[error("voter '{0}' is not registered")]
    UnregisteredVoter(String),

    #[error("voter '{0}' has already committed a ballot")]
    DoubleCommit(String),

    #[error("voter '{0}' has not committed a ballot")]
    NoCommitment(String),

    #[error("voter '{0}' has already revealed their ballot")]
    AlreadyRevealed(String),

    #[error("reveal does not match commitment for voter '{0}'")]
    InvalidReveal(String),

    #[error("tally requested before all reveals are in")]
    IncompleteReveals,
}
