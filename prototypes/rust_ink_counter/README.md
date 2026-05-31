# Rust Ink! Counter (prototype)

## Overview

**Rust_Ink_Counter** is a minimal ink! smart contract that exposes a stored `i32` with `get`, `increment`, and `decrement` messages. This is a **prototype**, not a portfolio piece — it lives under `prototypes/` for that reason. It demonstrates the basic ink! macro layout, the `#[ink(storage)]` / `#[ink(message)]` annotations, and saturating arithmetic. The full blockchain projects with real protocol mechanics live in [`blockchain_protocols/`](../../blockchain_protocols/).

## Key Features

- **Three Messages**: `get(&self) -> i32`, `increment(&mut self)`, `decrement(&mut self)`.
- **Saturating Arithmetic**: `i32::MAX + 1 == i32::MAX` instead of panicking. The original version used unchecked `+= 1` which would have aborted the contract on overflow.
- **Three Unit Tests**: init value, round-trip increment/decrement, saturating-arithmetic at both `i32::MAX` and `i32::MIN`.

## Architecture

```
Cargo.toml         ink! 4 dependencies (pulled from paritytech/ink, master)
src/lib.rs         The contract: storage, three messages, three unit tests
README.md
```

## Example Usage

After running `cargo test`, you can observe:

- **Initialization**: `RustInkCounter::new(0)` stores `0`.
- **Increment / Decrement**: each call adjusts the stored value by 1.
- **Saturating Safety**: incrementing `i32::MAX` does not panic the contract.

## Getting Started

### Prerequisites

- **Rust** (latest stable).
- **Cargo**.
- A Substrate / ink! development environment if you want to actually deploy: see the [ink! quickstart](https://use.ink/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/prototypes/rust_ink_counter
```

### Running

```bash
cargo build
```

### Testing

```bash
cargo test       # 3 unit tests
```

## Technical Specifications

- **Language**: Rust 2021
- **Smart-contract framework**: ink! (Substrate)
- **Storage**: a single `i32`
- **Arithmetic**: saturating
- **Test Coverage**: 3 unit tests

## What This Project Demonstrates

- **Familiarity with ink!** — the standard smart-contract framework for Substrate chains.
- **Defensive integer arithmetic** — saturating ops instead of unchecked `+=`.
- **Honest scoping** — labeled as a prototype, parked under `prototypes/`, not pretending to be a finished portfolio piece.

## Scope

- This is a counter, not a useful application. Real ink! work would include events, errors via `Result`, access control (only-owner pattern), and at minimum a couple of round-trip e2e tests.
- ink! has had several breaking releases; the `git = ".../ink", branch = "master"` dependency form here is fragile. A real project would pin to a tagged release (e.g. `"4.3.0"`).
- The arithmetic-saturation choice matters here, but in a real contract the saner default is probably `Result<(), Error>` returning an `Overflow` variant so the caller can react.

## Future Enhancements

- **Tagged ink! version**: pin to a released ink! version instead of `branch = "master"`.
- **Events**: emit a `Changed { old, new }` event from each mutator.
- **Access Control**: only-owner gating on `decrement` to demonstrate the access-control pattern.
- **End-to-End Tests**: a `tests/` directory with one `#[ink_e2e::test]` to exercise deployment + RPC calls.

## Contributing

Contributions welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries: lmdixon23@gmail.com.
