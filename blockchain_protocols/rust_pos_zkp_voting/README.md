# Rust PoS-ZKP Voting

## Overview

**Rust_PoS_ZKP_Voting** is a Rust simulation of a blockchain-based voting protocol that pairs Proof-of-Stake leader selection with Ed25519-signed votes and a SHA-256 commit-reveal step for eligibility. Every vote is cryptographically signed and verified against the voter's registered public key; every block is hash-integrity-protected and prev-hash-linked; and the chain exposes a tamper-detection check that any observer can run. The previous version of this code used MD5 (broken since 2004), accepted any string as a "ZKP" without checking it, and never verified signatures — see "Scope" for what is still a stand-in.

## Key Features

- **Proof-of-Stake Leader Selection**: Stake-weighted random sampling over active validators. Seeded via `Blockchain::with_seed` for deterministic tests.
- **Ed25519 Signature Verification**: Every vote is signed by the voter's secret key over a domain-separated message; `submit_vote` verifies the signature against the registered `VerifyingKey` and rejects forged votes.
- **Eligibility Commitments**: Each voter registers `SHA-256("eligibility:" || secret)`; their vote must include the secret as `eligibility_reveal`, which the chain rehashes and matches against the commitment.
- **Block Hash Integrity**: SHA-256 over a domain-separated block encoding. `verify_integrity()` walks the chain, rehashes each block, and verifies prev-hash linking — a unit test demonstrates that tampering with a single vote inside a sealed block causes the check to fail.
- **Append-Only Chain**: `mine_block` seals pending votes into a block tagged with the selected validator and the previous block's hash.

## Architecture

Rust `lib + bin` crate. The library exposes the `Blockchain` type and supporting primitives; the binary is a demo that registers voters, signs ballots, mines a block, and verifies integrity.

```
src/
  lib.rs         crate root + honest README of which primitives are real
  error.rs       ChainError (one variant per failure path)
  blockchain.rs  Block, SignedVote, Validator, Voter, Blockchain + 5 unit tests
  main.rs        Ed25519 demo: sign votes, mine block, tally, verify chain
Cargo.toml
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Voter Registration**: Voters register with a public key and a SHA-256 eligibility commitment.
- **Validator Registration**: Validators register with a stake amount; only active validators are eligible for selection.
- **Vote Submission**: Votes are signed locally, then submitted; the chain verifies signature + eligibility commitment + no-double-vote before accepting.
- **Consensus and Block Mining**: Stake-weighted leader selection picks the miner; the block is sealed with `prev_hash` and `hash`.
- **Vote Tallying**: All votes across the chain are summed by candidate.
- **Integrity Check**: `verify_integrity()` walks the chain to catch tampering.

## Getting Started

### Prerequisites

- **Rust** (latest stable). Install from [rust-lang.org](https://www.rust-lang.org/).
- **Cargo** (bundled with Rust).

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/blockchain_protocols/rust_pos_zkp_voting
```

### Running

```bash
cargo build
cargo run        # Ed25519 demo: sign votes, mine block, verify chain
```

### Testing

```bash
cargo test       # 5 unit tests
```

## Technical Specifications

- **Language**: Rust 2021
- **Consensus**: Proof-of-Stake (stake-weighted random sampling)
- **Cryptographic Hashing**: SHA-256 via `sha2` (replaced MD5)
- **Digital Signatures**: Ed25519 via `ed25519-dalek` v2
- **Random Number Generation**: `rand` 0.8 with `StdRng::seed_from_u64` for reproducible tests
- **Error Handling**: `thiserror`-derived `ChainError`
- **Test Coverage**: 5 unit tests covering happy path, forged signature, wrong eligibility reveal, double vote, and chain tamper detection

## What This Project Demonstrates

- Concrete understanding of **what makes a hash function "broken"**: MD5 was used as the block hash in the original code and the rewrite explicitly replaces it with SHA-256 with domain separation.
- Real **Ed25519 signature verification** wired into the validation path — not just a `String` field that gets logged and ignored.
- **Domain-separated message construction** (`"poa-zkp-voting/v1:" || ...`) so signatures from this protocol cannot be replayed in other contexts.
- **Tamper-evident chain design**: each block carries its own hash plus `prev_hash`, and the `verify_integrity()` test proves that a one-byte change inside a sealed block is detected.
- **Honest scoping**: the README explicitly calls out that the eligibility commitment is *not* a real ZKP, and a real ZKP would be a multi-month project; the rewrite gives the structural shape of an eligibility proof and labels it as such.

## Scope

- **The "ZKP" is a commit-reveal placeholder**, not zero-knowledge. A real ZKP voting scheme (Semaphore, groth16 ballots, etc.) would let the voter prove eligibility *without* revealing the secret.
- No P2P networking, no real validator gossip, no fork-choice rule, no slashing.
- The chain is in-memory only; there is no persistence layer.
- Stake values are static; there is no economic model for stake delegation, rewards, or punishment.

## Future Enhancements

1. **Real Zero-Knowledge Eligibility**: Wire in `arkworks` / `bellman` to produce a real Groth16 proof of eligibility membership. The headline gap — Scope flags the current commit-reveal as a ZKP *placeholder*, not zero-knowledge.
2. **Slashing for Validator Misbehavior**: Penalize validators who try to seal an invalid block.
3. **On-Chain Smart Contracts**: A scripting layer for vote-tally automation.

## Contributing

I welcome contributions from the community to enhance the features, security, and performance of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.
