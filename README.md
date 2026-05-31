# My Dev Projects

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
<!-- TODO: add CI badge after first green workflow run on GitHub:
     ![CI](https://github.com/lmdixon23/my_dev_projects/actions/workflows/ci.yml/badge.svg) -->

<!--
  REPO DESCRIPTION (for the one-liner under the repo name on GitHub —
  edit at https://github.com/lmdixon23/my_dev_projects → Settings → repo description):
    "Working portfolio: AI engineering, ML, blockchain protocols, data engineering, BI.
     Every project ships tests, smoke pipelines, and honest limitations."
-->

A working portfolio of production-shaped projects across AI engineering, machine learning, blockchain protocols, data engineering, network security, and business intelligence. Every project here has a working build, a real test suite or smoke pipeline, and an honest README that distinguishes what's implemented from what's aspirational.

## Start here (30-second tour)

- **For AI / ML engineering roles**, open [`ai_engineering/rag_assistant/README.md`](./ai_engineering/rag_assistant/) and [`ai_engineering/rlvr/grpo_minimal/README.md`](./ai_engineering/rlvr/grpo_minimal/) — the RAG system and the GRPO Figure-5 reproduction are the two highest-density pieces.
- **For systems / Rust / crypto roles**, open [`blockchain_protocols/rust_cross_chain_atomic_bridge/README.md`](./blockchain_protocols/rust_cross_chain_atomic_bridge/) — HTLC commit/reveal with constant-time comparison, full test suite.
- **For data engineering roles**, open [`data_engineering/sales_data_etl_ssis/README.md`](./data_engineering/sales_data_etl_ssis/) for the SSIS package + cross-platform Python-reference ETL.
- **For everything else**, the [Featured Projects](#featured-projects) section below has every project grouped by domain.

## Why this repository matters

This is not a collection of tutorial-fork notebooks. Each project demonstrates a concrete engineering skill — a working algorithm, a tested protocol, a deployable service, or a verifiable analytical pipeline — and ships with the scaffolding (tests, Docker, CI) that distinguishes a portfolio piece from a script. Where a real-world version of the system would require infrastructure I don't have (a TPU farm, a real blockchain, a SQL Server cluster, a paid OpenAI quota), the project ships an end-to-end **smoke pipeline** that exercises the code path on synthetic or in-repo data so reviewers can verify the work in under a minute.

## How this repository is organized

| Folder | Theme | Project count |
|---|---|---|
| [`ai_engineering/`](./ai_engineering/) | Modern LLM systems: RAG, agents, evals, an LLM-API CLI; plus RLVR-operator companion code | 4 + 2 |
| [`machine_learning/`](./machine_learning/) | Classical and deep ML, CV, NLP | 4 |
| [`blockchain_protocols/`](./blockchain_protocols/) | Rust protocol implementations | 6 |
| [`data_engineering/`](./data_engineering/) | ETL, warehousing, analytics | 1 |
| [`network_security/`](./network_security/) | Cloud security infrastructure | 1 |
| [`ai_playgrounds/`](./ai_playgrounds/) | Twelve single-file HTML+JS interactive applets for teaching core AI ideas | 12 |
| [`prototypes/`](./prototypes/) | Sketches and experiments, intentionally below portfolio bar | varies |

Every project has the same five-section README structure: **Overview**, **Key Features**, **Architecture**, **Example Usage**, **Getting Started** (with **Prerequisites / Installation / Running / Testing**), then **Technical Specifications**, **What This Project Demonstrates**, **Scope** (what this version is and is not — kept explicit because reviewers will check), and **Future Enhancements**.

<a id="featured-projects"></a>
## Featured projects

### AI Engineering ([`ai_engineering/`](./ai_engineering/))

- **[RAG Assistant](./ai_engineering/rag_assistant/)** — Document chunking, embedding, FAISS-backed vector store, retrieval + generation, and a retrieval-quality eval harness. The 2026-default pattern for grounding LLMs in your own documents.
- **[Agent Toolkit](./ai_engineering/agent_toolkit/)** — ReAct-style LLM agent with a typed tool registry (`@tool` decorator), trace logging, structured tool calls, and an AST-allowlisted expression evaluator for the built-in calculator (no `eval()`).
- **[LLM Eval Harness](./ai_engineering/llm_eval_harness/)** — Test-case format, four evaluator strategies (exact match, regex, embedding similarity, LLM-as-judge), aggregation, and an HTML report. The complement to RAG and agents that lets you actually measure them.
- **[NLP Text Summarization CLI](./ai_engineering/nlp_text_summarization_api/)** — Async OpenAI client with proper concurrency control, API-key rotation on 429, SQLite persistence, real trend analysis, tokenizer-free test suite via `httpx.MockTransport`.
- **[Regularized Operator Zoo](./ai_engineering/rlvr/regularized_operator_zoo/)** — Pedagogical implementations of the regularized greedy operators at the heart of modern RL post-training (negative entropy, KL-to-uniform, KL-to-anchor / Vieillard, Tsallis / sparsemax, Rényi). Companion code for my [RLVR Operator Series](https://github.com/lmdixon23/rlvr-operator-series) articles.
- **[GRPO Minimal](./ai_engineering/rlvr/grpo_minimal/)** — RFT, Online RFT, and GRPO+OS on a synthetic verifiable-reward task, sharing a single training loop. Reproduces the qualitative ranking from Figure 5 of Shao et al. 2024 (arXiv:2402.03300v3). Imports `kl_anchor_term` from the operator zoo — the load-bearing bridge between the two projects.

### Machine Learning ([`machine_learning/`](./machine_learning/))

- **[Image Captioning (CNN + RNN, TPU)](./machine_learning/image_captioning_cnn_rnn_tpu/)** — VGG16 encoder + LSTM decoder on COCO Val2017, real TPU strategy with CPU/GPU fallback, BLEU-4 evaluation.
- **[Image Classification](./machine_learning/image_classification/)** — Transfer learning with frozen VGG16, real test/train split, Dockerized Flask serving, three test files, smoke pipeline.
- **[Predictive Maintenance for Li-Ion Batteries](./machine_learning/predictive_maintenance/)** — Random Forest with persisted scaler + feature-column manifest, Flask serving that respects the training contract.
- **[Sentiment Analysis with BERT](./machine_learning/sentiment_analysis_transfer_learning/)** — Hugging Face `TFAutoModelForSequenceClassification` fine-tuning, three data loaders, network-free fast tests, smoke pipeline using `prajjwal1/bert-tiny`.

### Blockchain Protocols ([`blockchain_protocols/`](./blockchain_protocols/))

All Rust, all `lib + bin` with integration tests under `tests/`, all honest about being simulations rather than real on-chain code.

- **[Cross-Chain Atomic Bridge](./blockchain_protocols/rust_cross_chain_atomic_bridge/)** — HTLC commit/reveal with constant-time comparison, two-phase atomicity with rollback, native-vs-wrapped accounting.
- **[Decentralized Voting](./blockchain_protocols/rust_decentralized_voting/)** — SHA-256 commit-reveal ballots, Merkle root over the committed-ballot set for cross-observer verifiability.
- **[Quadratic Voting + Liquid Democracy](./blockchain_protocols/rust_quadratic_voting/)** — QV `n²` cost, credit-moving delegation, cycle detection at delegate-time.
- **[PoS + ZKP Voting](./blockchain_protocols/rust_pos_zkp_voting/)** — Stake-weighted PoS leader selection, real Ed25519-signed votes, eligibility commitments, tamper-evident chain.
- **[PoA + ZKP Voting](./blockchain_protocols/rust_poa_zkp_voting/)** — Round-robin authority block production (Clique/Aura-style), authority-signed blocks; PoA sibling of the PoS project.
- **[DeFi Lending Protocol](./blockchain_protocols/rust_defi_lending_protocol/)** — `u128` micro-unit money math, time-based interest accrual, utilization-driven dynamic rate, liquidation primitive, append-only event ledger.

### Data Engineering ([`data_engineering/`](./data_engineering/))

- **[Sales Data ETL (SSIS)](./data_engineering/sales_data_etl_ssis/)** — SSIS package with error redirect and row-count logging, idempotent SQL DDL + SQL Server Agent setup, plus a Python reference ETL targeting SQLite so the logic is verifiable on any machine.

### Network Security ([`network_security/`](./network_security/))

- **[SSE Coexistence Testing](./network_security/sse_coexistence_testing/)** — Terraform-managed AWS infrastructure for testing Security Service Edge / Global Secure Access coexistence with pfSense.

### AI Playgrounds ([`ai_playgrounds/`](./ai_playgrounds/))

Twelve single-file HTML+JavaScript interactive applets — no build step, no install, GitHub-Pages deployable — that map to the most visually-rich units of an introductory AI course. Built as a teaching companion for the 2025–2026 *Introduction to AI* curriculum at Haidian Kaiwen Academy, but free for any classroom to use.

Each applet targets a single "aha" moment — examples include A* vs BFS (search), Bayes-rule for rare diseases (probability), k in KNN (supervised), polynomial overfitting (evaluation), a TF-Playground-style tiny network (neural nets), k-means iteration (unsupervised), 3×3 convolution kernels (CV), and Q-learning gridworld (RL), plus logic/SAT, Bayesian networks, local search, and the Wumpus World. Drag a slider, the visualization re-renders live. See [`ai_playgrounds/README.md`](./ai_playgrounds/) for the full list and deployment guide.

### Business Intelligence — archived ([`archive/business_intelligence/`](./archive/business_intelligence/))

Earlier work, kept for provenance rather than active development. Power BI reports and the underlying data models — seven dashboards covering competitive marketing, customer profitability, HR, procurement, retail, sales & marketing, and supplier quality. Each `.pbix` ships with its source `.xlsx` so reviewers can open and refresh without external connections.

## Continuous integration

Each pushed commit triggers a workflow in [`.github/workflows/`](./.github/workflows/) that builds and tests every project. The matrix runs Python tests for the ML / AI / data-engineering projects, Cargo tests for the Rust crates, and Terraform validation for the network-security infrastructure.

## Results

Smoke-pipeline outputs (qualitative rankings, identity checks, expected metric ranges) for each runnable project are indexed in [`RESULTS.md`](./RESULTS.md). Each report has a one-line regenerate command so a reviewer can refresh the numbers with the real values from their own machine.

## Repository conventions

- **One README per project**, all in the same template, all linked from the relevant section above.
- **Tests live next to the code**: `tests/` directory in Python projects, `tests/integration.rs` for Rust crates, `python_reference_etl/` for the SSIS project.
- **Secrets via `.env`**, never committed. Each project that needs them ships a `.env.example`.
- **Smoke pipelines** (`smoke/run_smoke.py` or equivalent) wherever a full real-world run requires resources I don't have. These exercise the entire code path on synthetic or in-repo data.
- **No `venv/` checked in** — see the root `.gitignore`.

## Contributing

Contributions are welcome. Open an issue first if you're planning a substantial change so we can align on scope.

## License

This repository is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.

## Contact

For inquiries or collaboration: [lmdixon23@gmail.com](mailto:lmdixon23@gmail.com).

**Logan M. Dixon**
