//! Toy PoA (Proof-of-Authority) + commit-reveal voting chain.
//!
//! This is the Proof-of-Authority sibling of `rust_pos_zkp_voting`. The two
//! projects share the same voting/eligibility/signature machinery and differ
//! **only** in how a block producer is chosen — which is exactly the axis on
//! which PoA and PoS differ:
//!
//! - **PoA (this crate)**: block production rotates through a *fixed, named,
//!   pre-authorized* validator set in a deterministic **round-robin** order.
//!   Trust comes from *identity* — each block is signed by the authority whose
//!   turn it is, and the chain rejects a block sealed by anyone else. There is
//!   no stake and no randomness in selection. This is the Clique/Aura model.
//! - **PoS (sibling crate)**: block production is granted by *stake-weighted
//!   random sampling*. Trust comes from *economic skin in the game*, not
//!   identity.
//!
//! What is the same in both:
//!
//! - **Ed25519-signed votes**: every vote is signed by the voter's secret key
//!   over a domain-separated message and verified against the registered
//!   public key.
//! - **"ZKP" placeholder**: a SHA-256 commit-reveal over the voter's secret
//!   nonce. This is **not** a real zero-knowledge proof — a real ZKP would let
//!   a voter prove eligibility *without* revealing the secret. What this gives
//!   you is the *structural shape* of a ZKP step (a verifier consulting a
//!   commitment), with an honest caveat in the docs. See README "Scope".
//! - **Hash-linked blocks** with a tamper-detection walk any observer can run.
//!
//! Single-process, in-memory simulation. Not a real blockchain client.

pub mod blockchain;
pub mod error;

pub use blockchain::{
    eligibility_commit, Authority, Block, Blockchain, SignedVote, Voter,
};
pub use error::ChainError;
