# Rust DeFi Lending Protocol

## Overview

**Rust_DeFi_Lending_Protocol** is a Rust simulation of a collateralized lending market with **time-based interest accrual**, a **utilization-driven dynamic interest rate**, **liquidation of underwater loans**, and an **append-only event ledger**. All money is tracked in integer micro-units (1 unit = 1,000,000 micro-units) to avoid the floating-point rounding bugs that ate the previous version, and every state transition is observable via the `Ledger`.

## Key Features

- **Collateralized Loans**: Borrowing requires 150% collateral up front (`INITIAL_COLLATERAL_RATIO_BPS = 15_000`).
- **Dynamic Interest Rate**: `rate = base + slope * utilization` where `utilization = total_borrowed / total_supplied`. The rate is recomputed on every `current_rate_bps()` call and stamped onto each loan at open time.
- **Time-Based Interest Accrual**: `Loan::accrued_interest(now_tick)` uses simple-interest accrual; a unit test verifies the math against an explicit closed-form expectation.
- **Liquidation**: Anyone can call `liquidate(loan_id, liquidator_id)` when outstanding debt exceeds `collateral * 1.20`. Liquidator receives the collateral; the loan is marked liquidated and removed from total borrowed.
- **Append-Only Event Ledger**: Every `Register / Deposit / Withdraw / Borrow / Repay / Liquidate` is recorded so the system has a "transparent, tamper-resistant" trail.
- **Integer Money Math**: `u128` micro-units throughout; no `f64`.

## Architecture

Rust `lib + bin` crate. Library exposes `Protocol`, `Loan`, `User`, `Ledger`, `LedgerEvent`; the binary is a full borrow-accrue-repay-liquidate demo.

```
src/
  lib.rs           crate root + money / accrual semantics docs
  error.rs         LendingError (structured `have`/`need` fields)
  ledger.rs        LedgerEvent enum + append-only Ledger
  protocol.rs      Protocol: register / deposit / borrow / repay / liquidate
                   + 5 unit tests (collateral, accrual, liquidation, dynamic rate)
  main.rs          end-to-end borrow + accrue + repay + liquidate demo
tests/
  integration.rs   ledger-shape + unknown-loan handling (2 tests)
Cargo.toml
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **User Registration**: Users register with an initial balance; the total-supplied pool is updated.
- **Collateral Deposit**: Users move funds from `balance` to `collateral_locked`.
- **Loan Request**: A loan opens iff the user has 150% collateral; collateral is locked, principal is credited to balance, the loan's interest rate is stamped from `current_rate_bps()`, and the total-borrowed pool grows.
- **Time Passes**: `advance_time(ticks)` accrues simple interest on every active loan.
- **Loan Repayment**: Borrower pays `principal + accrued_interest`; collateral is unlocked.
- **Collateral Liquidation**: If accrued interest pushes outstanding past `collateral * 1.20`, any actor can call `liquidate`; the liquidator receives the collateral and the loan is closed.

## Getting Started

### Prerequisites

- **Rust** (latest stable). Install from [rust-lang.org](https://www.rust-lang.org/).
- **Cargo** (bundled with Rust).

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/blockchain_protocols/rust_defi_lending_protocol
```

### Running

```bash
cargo build
cargo run        # full borrow / accrue / repay / liquidate demo
```

### Testing

```bash
cargo test       # 5 unit + 2 integration = 7 tests
```

## Technical Specifications

- **Language**: Rust 2021
- **Money Type**: `u128` in micro-units (1 unit = 1,000,000 micro-units)
- **Interest Model**: Simple-interest accrual against a tick clock (`BPS_DENOM` ticks = 1 "year")
- **Rate Model**: `base_bps + slope_bps_per_bps * utilization_bps / BPS_DENOM`
- **Liquidation Threshold**: `outstanding > collateral * 1.20`
- **Error Handling**: `thiserror`-derived `LendingError` with structured fields
- **Test Coverage**: 5 unit + 2 integration = 7 tests

## What This Project Demonstrates

- **Money is integers**, not floats — the rewrite explicitly replaces every `f64` in the original with `u128` micro-units to avoid the canonical financial-software bug.
- Time-aware accounting via a `now_tick` clock the test can advance deterministically, instead of "interest applied once per repay call".
- A **utilization-driven rate curve** that reproduces the qualitative behavior of Aave / Compound (rate rises as the pool gets borrowed against).
- A **liquidation primitive** any actor can call when a position goes underwater — the foundational DeFi safety mechanism.
- An **append-only event ledger** as the auditability primitive, with a structured `enum` per event type instead of free-form strings.
- Idiomatic Rust: structured errors via `thiserror`, integer math with `saturating_*`, `lib + bin` separation, integration tests under `tests/`.

## Scope

- This is **not a real blockchain**. The "transparency" is an in-memory append-only `Vec`, not an on-chain ledger. A natural next step is to hash each event into a Merkle root (see `rust_decentralized_voting/src/merkle.rs` for that pattern).
- **Single-asset only**. Real protocols deal with multiple borrowed/lent assets with per-pair rates and oracles.
- **No liquidation bonus**. Real protocols pay liquidators a 5-10% discount on seized collateral to keep the mechanism actively used.
- **No price oracle**. Collateral is denominated in the same unit as the loan, so there is no notion of an external asset price moving.

## Future Enhancements

1. **Price Oracle Integration**: External price feed so collateral can drift below the loan in real economic terms. Today liquidation is reachable *only* via interest accrual (collateral value is static without an oracle, per Scope), so this is what makes the 120% threshold economically meaningful.
2. **Liquidation Incentive**: Pay liquidators a 5% bonus to keep the mechanism active — without it, the liquidation path exists but has no economic actor motivated to call it.
3. **Multi-Asset Support**: Per-asset pools with per-pair interest curves.
4. **Improved Risk Management**: Health factor + collateral factor per asset, à la Aave V3.

## Contributing

I welcome contributions from the community to enhance the features, security, and performance of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.
