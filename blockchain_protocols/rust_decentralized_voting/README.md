# Rust Decentralized Voting

## Overview

**Rust_Decentralized_Voting** is a commit-reveal voting protocol implemented in Rust, designed to be secure, anonymous-until-tally, and tamper-evident. Voters publish a `SHA-256(candidate || nonce)` commitment during voting and reveal `(candidate, nonce)` only at tally time; the system rejects any reveal whose hash does not match the original commitment. A Merkle root over the committed-ballot set gives independent observers a verifiable way to check they saw the same election state.

## Key Features

- **Anonymous-until-Tally Voting**: Only `SHA-256("ballot:" || candidate || nonce)` is published during the commit phase, so an observer of the network cannot determine who voted for what.
- **Tamper-Evident Reveals**: A coerced operator cannot rewrite ballots between commit and reveal — the rehash check rejects mismatches, and failed reveals do not consume the ballot (the voter can still reveal correctly).
- **Double-Vote Prevention**: One commitment per registered voter, one reveal per commitment, both enforced by the `BallotBox`.
- **Verifiable Tally**: `tally()` returns counts plus a Merkle root over the ordered committed-ballot set. Two independent observers tallying the same committed set get the same root.
- **Domain-Separated Hashing**: `"ballot:"` prefix on every commitment prevents collision with other SHA-256 uses elsewhere in the system.

## Architecture

Rust `lib + bin` crate. The library exposes `BallotBox`, `Commitment`, `Reveal`, `TallyResult`, and the Merkle utilities; the binary is a demo runner.

```
src/
  lib.rs       crate root + protocol docs
  error.rs     VotingError
  merkle.rs    Minimal Bitcoin-style Merkle root over 32-byte leaves (3 unit tests)
  ballot.rs    BallotBox: register / commit / reveal / tally (5 unit tests)
  main.rs      demo binary
tests/
  integration.rs   2 end-to-end tests
Cargo.toml
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Voter Registration**: Voters are registered by ID with the `BallotBox`.
- **Vote Commit (Phase 1)**: Each voter publishes `SHA-256("ballot:" || candidate || nonce)`. Their candidate choice is not yet visible to any observer.
- **Vote Reveal (Phase 2)**: Voters publish `(candidate, nonce)`; the box verifies the rehash matches the commitment and counts the ballot.
- **Tally**: Counts per candidate, total committed, total revealed, and a Merkle root over the ordered commitment set are returned.

## Getting Started

### Prerequisites

- **Rust** (latest stable). Install from [rust-lang.org](https://www.rust-lang.org/).
- **Cargo** (bundled with Rust).

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/blockchain_protocols/rust_decentralized_voting
```

### Running

```bash
cargo build
cargo run        # commit/reveal demo + tally + Merkle root
```

### Testing

```bash
cargo test       # 5 ballot + 3 merkle unit + 2 integration = 10 tests
```

## Technical Specifications

- **Language**: Rust 2021
- **Cryptographic Primitives**: SHA-256 via `sha2`
- **Tree Construction**: Bitcoin-style Merkle root (duplicate last on odd levels)
- **Error Handling**: `thiserror`-derived `VotingError`
- **Test Coverage**: 10 tests across 3 modules

## What This Project Demonstrates

- Understanding of the **commit-reveal pattern** — the standard cryptographic primitive for hiding ballot content while preserving auditability.
- **Domain-separated hashing** (`"ballot:"` prefix) to prevent collisions with other uses of SHA-256 in the same system.
- **Merkle anchoring** as a verifiability primitive — two observers can independently confirm they saw the same election state.
- Defensive design: a failed reveal does not consume the ballot, so an honest voter who fat-fingered their nonce isn't disenfranchised.
- Idiomatic Rust: `thiserror` for errors, `lib + bin` structure, integration tests under `tests/`.

## Scope

- This is a single-process in-memory simulation. There is no P2P network, no consensus, no on-chain anchoring of the Merkle root.
- "Anonymous-until-tally" hides the candidate choice from observers of the commitment, but does not provide unlinkable identity — a real anonymous-voting protocol would add ring signatures or zk-SNARKs.
- **Not coercion-resistant**: a voter who reveals their nonce to someone can prove how they voted. This is a known limitation of plain commit-reveal.

## Future Enhancements

1. **Enhanced Anonymity**: Add a Pedersen commitment + ring-signature layer to make voter identity itself unlinkable. Directly answers the top Scope caveat (commit-reveal hides the choice but not identity).
2. **Coercion Resistance**: Explore deniable encryption / receipt-free schemes (e.g. Civitas, JCJ), addressing the Scope note that plain commit-reveal lets a voter prove how they voted.
3. **Verifiability**: Add Merkle-inclusion proof generation so a voter can prove their ballot is in the tally without revealing the whole set. (Relabeled from "Scalability" — an inclusion proof buys succinct *verifiability*, not throughput; the `merkle.rs` root already exists to build on.)

## Contributing

I welcome contributions from the community to enhance the features, security, and performance of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.
