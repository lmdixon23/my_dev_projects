//! Commit-reveal voting protocol with SHA-256 ballot commitments.
//!
//! Anonymity model: voters publish a *commitment* `H(candidate || nonce)`
//! at vote time. The link between a voter and their candidate choice is
//! revealed only at tally time when the voter reveals their `(candidate,
//! nonce)`. The system rejects any reveal whose hash does not match the
//! commitment, so a corrupt operator cannot rewrite ballots between the
//! two phases.
//!
//! Double-vote prevention: each registered voter can only submit one
//! commitment (enforced by `BallotBox::commit`). Each commitment can only
//! be revealed once (enforced by `BallotBox::reveal`).
//!
//! Tally integrity: tallied results include a Merkle root over the
//! ordered list of `(voter_id, commitment)` pairs. Two independent
//! observers will compute the same root only if they saw the same set of
//! committed ballots. The root is the "verifiable by all participants"
//! piece referenced in the README.
//!
//! This is a single-process simulation. There is no network, no
//! consensus, no on-chain anchoring. The Merkle root would be the natural
//! handoff point to a real anchor (e.g. an Ethereum transaction).

pub mod ballot;
pub mod error;
pub mod merkle;

pub use ballot::{Ballot, BallotBox, Commitment, Reveal, TallyResult};
pub use error::VotingError;
