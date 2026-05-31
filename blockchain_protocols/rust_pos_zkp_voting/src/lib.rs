//! Toy PoS + commit-reveal voting chain.
//!
//! The previous version of this crate used MD5 (broken since 2004) for
//! block hashing, accepted any string as a "ZKP", and never verified
//! signatures. This rewrite swaps in real primitives that fit a portfolio
//! project:
//!
//! - **Block hash**: SHA-256 (not MD5).
//! - **Signatures**: Ed25519 (`ed25519-dalek`). Every vote is signed by
//!   the voter's secret key; the chain verifies the signature against the
//!   voter's registered public key before including the vote.
//! - **"ZKP" placeholder**: commit-reveal over the voter's secret nonce.
//!   This is **not** a real ZKP — a real ZKP would let the voter prove
//!   eligibility without revealing identity. What this gives you is the
//!   *structural shape* of a ZKP step (a verifier that consults a
//!   commitment), with an honest caveat in the docs.
//! - **PoS leader selection**: stake-weighted random sampling, same as
//!   the original. Cleaned up to be deterministic given an RNG seed (used
//!   in tests).
//! - **Chain integrity**: each block carries `prev_hash`, and the chain
//!   exposes `verify_integrity()` so observers can detect tampering.

pub mod blockchain;
pub mod error;

pub use blockchain::{Block, Blockchain, SignedVote, Validator, Voter};
pub use error::ChainError;
