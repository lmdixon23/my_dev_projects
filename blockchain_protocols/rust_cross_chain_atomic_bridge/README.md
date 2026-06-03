# Rust Cross-Chain Atomic Bridge

## Overview

**Rust_Cross_Chain_Atomic_Bridge** is a Rust simulation of an HTLC-based atomic-swap bridge between two or more in-process "chains". The point of the project is to demonstrate the protocol mechanics of a cross-chain bridge — preimage commit/reveal, two-phase atomicity with rollback, native vs wrapped asset tracking, and audit logging — in working code that compiles, runs, and is exercised by integration tests. It is **not** a connection to Ethereum, Polkadot, or any real network; see "Scope" below for what is deliberately not modeled.

## Key Features

- **Atomic Swaps**: `Htlc::commit(preimage, duration)` stores `SHA-256(preimage)` and the expiry; `Htlc::verify` re-hashes at claim time with `subtle::ConstantTimeEq` to prevent timing attacks.
- **Multi-Chain Support**: `Bridge::register` accepts any number of in-process `MockChain` instances by name.
- **Cross-Chain Messaging Boundary**: Every protocol step that crosses a chain boundary is marked with an explicit `MessageSent` / `MessageReceived` audit event — so the simulation is honest about where a real relayer / light-client would live.
- **Two-Phase Atomicity with Rollback**: The transfer flow is lock -> message -> mint-wrapped -> message -> release. If the user does not reveal the preimage before timeout, `rollback_transfer` burns the wrapped representation and refunds the source-chain lock.
- **Native vs Wrapped Distinction**: Holdings carry a `HoldingKind` tag (`Native` or `Wrapped { origin }`).
- **Conservation Invariant (at-rest)**: `Bridge::total_value` sums holdings across all chains; the end-to-end test asserts the sum is preserved across a completed transfer.
- **Auditing**: `AuditLog` is append-only, timestamped, and queryable.

## Architecture

Standard Rust `lib + bin` crate. The `lib` exposes the protocol primitives; the `bin` is a demo that wires two `MockChain`s together and runs a transfer. Integration tests under `tests/` exercise the public API end-to-end.

```
src/
  lib.rs           crate root, re-exports
  error.rs         BridgeError
  htlc.rs          Htlc + 3 unit tests
  audit.rs         AuditEvent, AuditLog
  chain.rs         Asset, HoldingKind, Holding, Lock, MockChain + 3 unit tests
  bridge.rs        Bridge, bridge_transfer, rollback_transfer
  main.rs          demo binary
tests/
  integration.rs   3 end-to-end tests through the public API
Cargo.toml
```

## Example Usage

Running the demo binary walks through these steps:

- **Asset Registration**: Native assets are deposited on a source `MockChain` with a unique identifier.
- **HTLC Creation**: A Hashed TimeLock Contract is created for the transfer, locking the source asset under `hash(preimage)` with a timeout.
- **Cross-Chain Transfer**: An explicit `MessageSent("LockObserved")` audit event marks the source-to-dest boundary; the destination mints the wrapped representation.
- **Preimage Reveal**: The reverse boundary message (`PreimageRevealed`) triggers source-side release once the rehashed preimage matches the commitment.
- **Logging and Auditing**: All eight events of a successful transfer are visible in the `AuditLog`.

## Getting Started

### Prerequisites

- **Rust** (latest stable). Install from [rust-lang.org](https://www.rust-lang.org/).
- **Cargo** (bundled with Rust).

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/blockchain_protocols/rust_cross_chain_atomic_bridge
```

### Running

```bash
cargo build
cargo run                  # runs the demo binary
RUST_LOG=info cargo run    # also prints per-event debug logs
```

### Testing

```bash
cargo test                 # 6 unit tests + 3 integration tests
```

## Technical Specifications

- **Language**: Rust 2021
- **Async runtime**: tokio
- **Cryptographic Hashing**: SHA-256 via `sha2`
- **Constant-Time Comparison**: `subtle`
- **Error handling**: `thiserror`-derived `BridgeError`
- **Identifiers**: `uuid` v4 for lock IDs
- **Test Coverage**: 6 unit + 3 integration = 9 tests

## What This Project Demonstrates

- The **HTLC primitive** and the commit/reveal mechanic that makes atomic swaps trustless.
- **Two-phase protocol design with rollback**: the integration tests explicitly verify that no execution path leaves a source asset released without the wrapped being minted, or vice versa.
- **Constant-time cryptographic comparison** — `subtle::ConstantTimeEq` instead of `==`, the same pattern used in real wallets and signature libraries.
- Architectural honesty: cross-chain message boundaries surface as audit events rather than being hidden inside the same `tokio::Mutex`, keeping the simulation upfront about where a real relayer would live.
- Idiomatic Rust: `Arc<Mutex<…>>` for shared chain state, `thiserror` for ergonomic error types, integration tests under `tests/` (the Cargo convention).

## Scope

This is a learning artifact, not a real bridge. Specifically, the following are **not** modeled (and would each be substantial work to add):

- Real consensus, finality, and light-client verification.
- Signature schemes for relayers and validators.
- Validator sets, slashing, and economic security.
- Gas accounting and fee markets.
- Resistance to long-range reorgs.
- Multi-asset atomic swaps in a single HTLC.
- Reverse-direction (burn-and-release) transfers — the data model supports them, but no top-level function is exposed.

## Future Enhancements

1. **Reverse-direction transfers** using the existing `HoldingKind::Wrapped { origin }` tag — the data model already supports it; only a top-level function is missing.
2. **Property-based testing** (proptest) for the conservation invariant (`lib.rs`) under interleaved transfers. Cheap, high-signal: it turns a stated invariant into a machine-checked one.
3. **Signature verification on cross-chain messages** with Ed25519 keys for relayers. (Future — no signature crate is wired in yet; the README describes this in future tense.)
4. **Timelock-refund path**: expose the HTLC's expiry-refund branch so a locked asset can be reclaimed after timeout — the safety half of an atomic swap.

Licensed under the [MIT License](https://github.com/lmdixon23/my_dev_projects/blob/main/LICENSE).
