# Rust PoA-ZKP Voting

## Overview

**Rust_PoA_ZKP_Voting** is a Rust simulation of a blockchain-based voting protocol whose block producer is chosen by **Proof-of-Authority (PoA)**: a fixed, pre-authorized validator set takes turns sealing blocks in deterministic round-robin order, and each block carries the Ed25519 signature of the authority whose turn it was. It is the PoA sibling of [`rust_pos_zkp_voting`](../rust_pos_zkp_voting/); the two share the same voting, eligibility, and signature machinery and differ only in producer selection — the single axis on which PoA and PoS actually differ. As with the sibling, votes are Ed25519-signed and verified against the voter's registered key, blocks are hash-linked, and any observer can run a tamper-detection walk. This is a single-process, in-memory simulation, not a real blockchain client.

## PoA vs. PoS — the one real difference

| | PoA (this project) | PoS (sibling) |
|---|---|---|
| Who may produce a block | a fixed, named, pre-authorized set | anyone with stake |
| Selection rule | deterministic **round-robin** | **stake-weighted random** sampling |
| Source of trust | validator **identity** (signed blocks) | **economic stake** at risk |
| Permissioning | permissioned / consortium | permissionless |

Everything else in the two crates is intentionally identical, so a reader can diff them and see exactly what the consensus choice changes.

## Key Features

- **Round-Robin Authority Selection**: block `k` is produced by `sorted_authorities[k mod n]`. Deterministic and reproducible — no RNG in the selection path.
- **Authority-Signed Blocks**: `mine_block` requires the signing key of the scheduled authority and rejects any out-of-turn or unauthorized key (`WrongProposer`). Each block stores the proposer id and its Ed25519 signature over the block hash.
- **Ed25519 Vote Verification**: every vote is signed by the voter over a domain-separated message; `submit_vote` verifies it against the registered `VerifyingKey` and rejects forgeries.
- **Eligibility Commitments**: each voter registers `SHA-256("eligibility:" || secret)` and must reveal the secret in their vote, which the chain re-hashes and matches. (A commit-reveal placeholder for a real ZKP — see Scope.)
- **Tamper-Evident Chain**: `verify_integrity()` rehashes each block, checks prev-hash linking, checks the round-robin schedule, and verifies each proposer signature; a unit test shows that mutating one sealed vote breaks the check.

## How to Run

```bash
cd my_dev_projects/blockchain_protocols/rust_poa_zkp_voting
cargo run     # runs the demo in src/main.rs
cargo test    # runs the unit tests in src/blockchain.rs
```

## Technical Specifications

- **Language**: Rust (edition 2021)
- **Crypto**: `ed25519-dalek` 2.x (votes and blocks), `sha2` (block hashing, eligibility commitments)
- **Consensus**: round-robin over a `BTreeMap`-ordered authority set
- **Persistence**: none — in-memory `Vec<Block>` per process

## What This Project Demonstrates

- The concrete difference between PoA and PoS, reduced to a single swapped method (`current_proposer` / `mine_block`) against a shared codebase — so the consensus distinction is legible in code, not just prose.
- Authority identity enforced cryptographically: a block is only valid if signed by the authority the schedule names, and the chain proves it on replay.
- The same honest commit-reveal "ZKP placeholder" framing as the sibling, with the caveat kept in the docs rather than hidden.

## Scope

- **The "ZKP" is a commit-reveal placeholder**, not zero-knowledge. A real ZKP voting scheme (Semaphore, Groth16 ballots, etc.) would let the voter prove eligibility *without* revealing the secret.
- **Round-robin is the simplest PoA.** Production PoA (Clique, Aura) adds out-of-turn fallback proposers after a timeout, epoch-based authority-set changes, and difficulty/score rules to choose between competing in-turn vs. out-of-turn blocks. None of that is modeled here.
- The authority set is fixed at construction; there is no on-chain governance to add or evict authorities.
- In-memory only; no P2P, no networking, no persistence.

## Future Enhancements

1. **Authority Eviction / Governance**: let the authority set vote to add or remove a member, with the change taking effect at an epoch boundary — the PoA analogue of the PoS sibling's slashing item.
2. **Out-of-Turn Fallback Proposers**: after a timeout, allow the next authority in rotation to seal the block at reduced priority (Clique's in-turn vs. out-of-turn scoring), so a single offline authority cannot stall the chain.
3. **Real Zero-Knowledge Eligibility**: replace the commit-reveal with a Groth16 (`arkworks`) eligibility-membership proof, shared with the PoS sibling.

## References

- De Angelis, S., et al. (2018). *PBFT vs Proof-of-Authority: Applying the CAP Theorem to Permissioned Blockchain.*
- Szilágyi, P. (2017). *Clique PoA protocol & Rinkeby PoA testnet.* EIP-225.

## Contributing

I welcome contributions from the community to enhance the features, security, and performance of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries, please contact lmdixon23@gmail.com.
