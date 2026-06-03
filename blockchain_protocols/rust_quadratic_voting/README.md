# Rust Quadratic Voting

## Overview

**Rust_Quadratic_Voting** is a voting protocol implemented in Rust that combines **Quadratic Voting** (cost = `n_votes^2` credits per ballot) with **Liquid Democracy** (voters can delegate their credits to a trusted peer). Delegation transfers credits — it does not duplicate them — and the system actively rejects delegation cycles. The original version of this code had a real liquid-democracy bug where delegation silently no-op'd; this rewrite makes the semantics precise and testable.

## Key Features

- **Quadratic Voting**: A voter spending `n` votes for a candidate pays `n^2` credits, giving more nuanced control than equal-weight voting.
- **Liquid Democracy**: `delegate(a, b)` *moves* `a`'s remaining credits to `b` and prevents `a` from casting directly. Chained delegations `a -> b -> c` pool correctly.
- **Cycle Detection**: Any delegation that would close a cycle (`a -> b -> a`) is rejected with `DelegationCycle`.
- **Double-Delegation Prevention**: A voter who has already delegated cannot delegate again (rejected with `AlreadyDelegated`).
- **Split-Credit Ballots**: A voter can cast multiple ballots for different candidates; credits are deducted per-call until exhausted.
- **Saturating Arithmetic**: Credit transfers and quadratic cost computation use `saturating_add` / `saturating_mul` so adversarial inputs never trigger integer overflow.

## Architecture

Rust `lib + bin` crate. The library is one module (`voting`) with a single `VotingSystem` struct; the binary is a demo.

```
src/
  lib.rs           crate root + semantics docs
  error.rs         QvError
  voting.rs        VotingSystem + 9 unit tests
  main.rs          demo binary
tests/
  integration.rs   2 end-to-end tests (chained delegation, split ballots)
Cargo.toml
```

## Example Usage

The demo steps through registration, delegation, voting, and tally:

- **Voter Registration**: Voters register with an ID and an initial credit balance.
- **Delegation** (optional): A voter delegates their remaining credits to another voter; their credits become 0 and the delegate's credit balance increases.
- **Vote Submission**: A non-delegating voter casts `n` votes for a candidate, paying `n^2` credits.
- **Tally**: Counts per candidate plus total votes cast are returned.

## Getting Started

### Prerequisites

- **Rust** (latest stable). Install from [rust-lang.org](https://www.rust-lang.org/).
- **Cargo** (bundled with Rust).

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/blockchain_protocols/rust_quadratic_voting
```

### Running

```bash
cargo build
cargo run        # delegation + QV demo with tally
```

### Testing

```bash
cargo test       # 9 unit + 2 integration = 11 tests
```

## Technical Specifications

- **Language**: Rust 2021
- **Voting Theories**: Quadratic Voting, Liquid Democracy
- **Error Handling**: `thiserror`-derived `QvError`
- **Cycle Detection**: Linear-time walk of the delegation chain at delegate-time
- **Test Coverage**: 11 tests across two modules

## What This Project Demonstrates

- Precise modeling of two interacting voting mechanisms (QV + LD) without letting them quietly contradict each other.
- **Cycle detection as a correctness requirement**, not an afterthought. The integration test explicitly verifies that a 3-step cycle is rejected.
- **Saturating arithmetic** throughout the credit math, so adversarial inputs never produce undefined behavior or overflow panics.
- A **single-source-of-truth invariant**: `Voter::delegate` is the only place delegation state lives, ruling out the bug from the previous version (parallel `delegations` HashMap + dead `Voter::delegate` field).
- Idiomatic Rust: `lib + bin`, `thiserror`, integration tests under `tests/`.

## Scope

- This is an in-memory `HashMap`-backed implementation, not a sharded distributed system. The README's "scalability" framing is best read as "the algorithms scale", not "the deployment does".
- No cryptography — for verifiable QV results you'd want to anchor the tally in a Merkle root (see `rust_decentralized_voting/src/merkle.rs` for that pattern).
- Two delegation modes: `delegate(a, b)` is all-or-nothing; `delegate_n(a, b, k)` moves only `k` credits and lets the delegator keep voting with the rest.

## Future Enhancements

1. **Sybil Resistance**: Tie voter IDs to a proof-of-personhood layer so attackers can't farm credits with fake identities — the assumption quadratic voting's fairness rests on.
2. **Smart Contract Integration**: Anchor the tally in an on-chain Merkle root, reusing the pattern already implemented in `rust_decentralized_voting/src/merkle.rs` rather than building it greenfield.

> **Implemented** — _Partial delegation_: `delegate_n(from, to, k)` moves only `k` credits and preserves the delegator's voting rights over the remainder (`voting.rs`), closing the Scope note that `delegate` was all-or-nothing. Verified: `cargo test` reports 9 unit + 2 integration = 11/11 passing.

Licensed under the [MIT License](https://github.com/lmdixon23/my_dev_projects/blob/main/LICENSE).
