//! Quadratic Voting + Liquid Democracy.
//!
//! Quadratic Voting: a voter with `c` credits casting `n` votes for a
//! single candidate spends `n*n` credits. Casting two votes for two
//! different candidates is supported by calling `submit_vote` twice;
//! credits are deducted per call.
//!
//! Liquid Democracy: a voter can delegate their unused credits to
//! another voter. `delegate` is all-or-nothing — A keeps 0 credits and B's
//! casting power is increased by all of A's. `delegate_n(a, b, k)` moves only
//! `k` credits and lets A keep voting with the remainder. Delegation cycles
//! are rejected at `delegate` time.
//!
//! Note: the previous version of this code had a real bug — the
//! `delegate` field on `Voter` was set in one place (never), and read in
//! another (always), so liquid democracy silently no-op'd. See README1.md
//! for the rewrite rationale.

pub mod error;
pub mod voting;

pub use error::QvError;
pub use voting::{TallyResult, VotingSystem};
