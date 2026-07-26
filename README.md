# Engineering Portfolio

[![CI](https://github.com/lmdixon23/my_dev_projects/actions/workflows/ci.yml/badge.svg)](https://github.com/lmdixon23/my_dev_projects/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Rust: stable](https://img.shields.io/badge/rust-stable-orange.svg)](https://www.rust-lang.org/)
[![Live demos](https://img.shields.io/badge/live_demos-AI_Playgrounds-brightgreen.svg)](https://lmdixon23.github.io/ai-playgrounds/)

A curated monorepo of tested software projects across applied AI, reinforcement-learning post-training, machine learning, Rust protocol design, data engineering, and cloud security.

Every featured project includes its own setup instructions, validation path, and explicit scope boundaries. The root CI currently covers **17 projects: 10 Python projects, 6 Rust crates, and 1 Terraform configuration**.

## Start Here

| Area | Recommended entry point | Why it is useful |
|---|---|---|
| LLM systems | [RAG Assistant](./ai_engineering/rag_assistant/) | Modular retrieval and generation, FAISS with a NumPy fallback, retrieval evaluation, and optional cross-encoder re-ranking |
| RL post-training | [GRPO Minimal](./ai_engineering/rlvr/grpo_minimal/) and [Regularized Operator Zoo](./ai_engineering/rlvr/regularized_operator_zoo/) | A shared training loop for RFT, Online RFT, and GRPO+OS, backed by tested regularized operators |
| Rust systems | [Cross-Chain Atomic Bridge](./blockchain_protocols/rust_cross_chain_atomic_bridge/) | HTLC commit and reveal, rollback, conservation checks, native and wrapped asset accounting, and integration tests |
| Data engineering | [Sales Data ETL](./data_engineering/sales_data_etl_ssis/) | SSIS delivery artifacts plus a portable Python and SQLite reference path for CI verification |
| Browser demos | [AI Playgrounds](https://lmdixon23.github.io/ai-playgrounds/) | Twelve bilingual interactive AI applets in a separate repository with no installation required |

## Verified Results

### RAG retrieval and re-ranking

The checked-in five-case smoke benchmark produced the following CPU result:

| Configuration | recall@3 | MRR |
|---|---:|---:|
| Embedding retrieval | 1.000 | 0.900 |
| Cross-encoder re-ranked | 1.000 | 1.000 |
| Observed delta | +0.000 | +0.100 |

The re-ranker moved one relevant result from rank 2 to rank 1. This is a reproducible smoke measurement, not evidence of a general quality lift; [issue 18](https://github.com/lmdixon23/my_dev_projects/issues/18) tracks the larger discriminative benchmark.

### GRPO qualitative reproduction

On a synthetic verifiable-reward task, averaged across three seeds and 1,200 steps:

| Method | Final accuracy |
|---|---:|
| RFT | 0.181 |
| Online RFT | 0.945 |
| GRPO+OS | 0.990 |

The project reproduces the qualitative ordering **RFT < Online RFT < GRPO+OS** associated with Figure 5 of Shao et al. 2024. It does not claim the paper's absolute benchmark values.

### Regularized operator identities

A verified run of the operator library produced:

- maximum policy-to-gradient residual of `1.8e-07`;
- maximum conjugate-identity difference of `2.2e-16`.

See [RESULTS.md](./RESULTS.md) for the recorded run context and regeneration commands.

## Project Index

### AI and LLM Systems

| Project | Focus |
|---|---|
| [RAG Assistant](./ai_engineering/rag_assistant/) | Chunking, embeddings, vector search, cited generation, retrieval metrics, Flask serving, Docker, and optional cross-encoder re-ranking |
| [Agent Toolkit](./ai_engineering/agent_toolkit/) | ReAct-style agent loop, typed tool registry, deterministic test LLM, append-only traces, and guarded built-in tools |
| [LLM Eval Harness](./ai_engineering/llm_eval_harness/) | JSON and YAML evaluation suites, exact and regex grading, embedding similarity, LLM-as-judge, and standalone HTML reports |
| [NLP Text Summarization CLI](./ai_engineering/nlp_text_summarization_api/) | Async batching, concurrency limits, API-key rotation, SQLite persistence, and network-free HTTP-path tests |

### RL Post-Training and Mathematical Software

| Project | Focus |
|---|---|
| [Regularized Operator Zoo](./ai_engineering/rlvr/regularized_operator_zoo/) | Entropy, KL, Tsallis, and chi-squared regularized greedy operators with numerical identity checks |
| [GRPO Minimal](./ai_engineering/rlvr/grpo_minimal/) | RFT, Online RFT, and GRPO+OS on one training skeleton with a tested dependency on the operator library |

### Machine Learning

| Project | Focus |
|---|---|
| [Image Captioning](./machine_learning/image_captioning_cnn_rnn_tpu/) | VGG16 encoder, LSTM decoder, COCO loading, TPU strategy with fallback, BLEU-4 evaluation, and a CPU smoke run |
| [Image Classification](./machine_learning/image_classification/) | Frozen VGG16 transfer learning, held-out testing, Flask inference, Docker, and synthetic end-to-end validation |
| [Predictive Maintenance](./machine_learning/predictive_maintenance/) | Battery telemetry preprocessing, persisted feature contract, Random Forest training, evaluation, and Flask serving |

### Rust Protocol Simulations

These crates demonstrate protocol mechanics in tested, in-process simulations. They are not production blockchains or deployed smart contracts.

| Project | Focus |
|---|---|
| [Cross-Chain Atomic Bridge](./blockchain_protocols/rust_cross_chain_atomic_bridge/) | HTLC commit and reveal, explicit message boundaries, rollback, conservation, and asset representation |
| [Decentralized Voting](./blockchain_protocols/rust_decentralized_voting/) | Commit and reveal ballots plus Merkle-root verification |
| [Quadratic Voting and Liquid Democracy](./blockchain_protocols/rust_quadratic_voting/) | Quadratic credit costs, delegation, and cycle detection |
| [PoS and ZKP Voting](./blockchain_protocols/rust_pos_zkp_voting/) | Stake-weighted leadership, signed votes, eligibility commitments, and a tamper-evident chain |
| [PoA and ZKP Voting](./blockchain_protocols/rust_poa_zkp_voting/) | Authority rotation, signed blocks, and voting protocol mechanics |
| [DeFi Lending Protocol](./blockchain_protocols/rust_defi_lending_protocol/) | Fixed-precision accounting, interest accrual, utilization-based rates, liquidation, and append-only events |

### Data Engineering and Cloud Security

| Project | Focus |
|---|---|
| [Sales Data ETL](./data_engineering/sales_data_etl_ssis/) | SSIS package, validation and error routing, idempotent SQL setup, SQL Agent scheduling, and a portable Python reference ETL |
| [SSE Coexistence Testing](./network_security/sse_coexistence_testing/) | Terraform-managed AWS test environment, hardened host bootstrap, and post-deployment reachability checks |

Experimental work remains under [`prototypes/`](./prototypes/) and is intentionally excluded from the featured project count.

## Validation and Reproducibility

The root [GitHub Actions workflow](./.github/workflows/ci.yml) runs:

- test suites for 10 Python projects;
- `cargo build`, `cargo test`, and advisory Clippy checks for 6 Rust crates;
- `terraform init -backend=false` and `terraform validate` for the cloud-security configuration.

Projects that depend on external APIs, large datasets, TPU access, SQL Server, or AWS provide a network-free test path, a synthetic smoke pipeline, or a portable reference implementation where appropriate. Generated reports are excluded when values can drift between runs; commands and selected verified outputs are documented in project READMEs and [RESULTS.md](./RESULTS.md).

## Repository Boundaries

- Each project README distinguishes implemented behavior from future enhancements.
- Live OpenAI calls require user-supplied credentials; tests use deterministic or mocked paths.
- Rust blockchain projects model protocol behavior without claiming live-network security or consensus.
- Terraform is validated in CI, while deployment remains opt-in and may create billable cloud resources.
- Prototype directories are exploratory and are not represented as portfolio-complete projects.
- Secrets, local virtual environments, generated models, datasets, and runtime reports are excluded through repository ignore rules.

## Getting Started

There is no repository-wide dependency installation because the projects use different Python, Rust, Terraform, SSIS, and cloud toolchains.

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects
```

Choose a project from the index above and follow its README for installation, execution, testing, and scope.

## Related Repository

The interactive teaching applets formerly stored here now live in [lmdixon23/ai-playgrounds](https://github.com/lmdixon23/ai-playgrounds), with a [public browser demo](https://lmdixon23.github.io/ai-playgrounds/).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) before proposing a substantial change.

## Security

Report security concerns according to [SECURITY.md](./SECURITY.md).

## License

Licensed under the [MIT License](./LICENSE).
