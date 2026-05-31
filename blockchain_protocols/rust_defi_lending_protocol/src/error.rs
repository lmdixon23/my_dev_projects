use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum LendingError {
    #[error("user '{0}' is not registered")]
    UnknownUser(String),

    #[error("user '{user}' has insufficient balance (have {have}, need {need})")]
    InsufficientBalance { user: String, have: u128, need: u128 },

    #[error("user '{user}' has insufficient collateral (have {have}, need {need})")]
    InsufficientCollateral { user: String, have: u128, need: u128 },

    #[error("loan '{0}' does not exist or has been repaid/liquidated")]
    UnknownLoan(u64),

    #[error("loan '{0}' is not currently liquidatable")]
    NotLiquidatable(u64),
}
