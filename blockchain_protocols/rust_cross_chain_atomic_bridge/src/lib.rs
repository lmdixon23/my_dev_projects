//! # Rust Cross-Chain Atomic Bridge (Simulation)
//!
//! Single-binary simulation of an HTLC-based atomic-swap bridge between
//! two or more in-process "chains". This is **not** a connection to
//! Ethereum, Polkadot, or any real network — there are no nodes, no
//! consensus, no signatures, no on-chain smart contracts. What this code
//! demonstrates is the protocol mechanics that a real bridge would need:
//!
//! - **HTLC commit / reveal** with constant-time verification ([`Htlc`]).
//! - **Two-phase atomicity with rollback** via [`bridge::bridge_transfer`]
//!   and [`bridge::rollback_transfer`].
//! - **Multi-chain support**: any number of [`MockChain`] instances can be
//!   registered with a [`Bridge`].
//! - **Cross-chain messaging boundary** marked by explicit
//!   `MessageSent` / `MessageReceived` audit events.
//! - **Native vs wrapped distinction** via [`HoldingKind`].
//! - **Conservation invariant (at-rest)**: across all chains, the sum of
//!   native + wrapped of any asset before a completed transfer equals the
//!   sum after.
//! - **Auditing** via an append-only [`AuditLog`].
//!
//! What is still aspirational and would require real on-chain code:
//! consensus, finality assumptions, light-client verification, signature
//! checks, gas accounting, slashing of misbehaving relayers, resistance
//! to long-range reorgs. Those are not modeled.

pub mod audit;
pub mod bridge;
pub mod chain;
pub mod error;
pub mod htlc;

pub use audit::{AuditEvent, AuditLog};
pub use bridge::{bridge_transfer, rollback_transfer, Bridge};
pub use chain::{Asset, Holding, HoldingKind, Lock, LockState, MockChain};
pub use error::BridgeError;
pub use htlc::Htlc;
