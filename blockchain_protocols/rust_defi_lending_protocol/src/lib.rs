//! Collateralized lending simulation.
//!
//! All values are integer "micro-units" (1 unit = 1_000_000 micro-units)
//! to avoid the `f64` rounding bugs that ate the previous version. A
//! single in-memory `Protocol` instance tracks users, active loans, and
//! an append-only `Ledger` of events.
//!
//! Features that match the README:
//!
//! - **Collateralized loans**: borrow requires `principal *
//!   collateral_ratio_bps / 10_000` collateral to be locked.
//! - **Dynamic interest rate**: `interest_rate_bps = base + slope * utilization`,
//!   where `utilization = total_borrowed / total_supplied`. Recomputed on
//!   every state-changing call.
//! - **Loan repayment**: pay principal + accrued interest; collateral
//!   unlocks proportionally.
//! - **Liquidation**: if the collateral value falls below the loan's
//!   liquidation threshold, anyone can call `liquidate` to seize the
//!   collateral and clear the loan. Models the LTV check that Aave / Compound
//!   use.
//! - **Transaction transparency**: every state change appends to `Ledger`.

pub mod error;
pub mod ledger;
pub mod protocol;

pub use error::LendingError;
pub use ledger::{Ledger, LedgerEvent};
pub use protocol::{Loan, Protocol, User};
