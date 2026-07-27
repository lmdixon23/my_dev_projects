# Validation and Measured Results

This file separates measured outputs from reproducible execution paths. A passing test, a smoke pipeline, a portable reference implementation, and a real-model metric are different forms of evidence and are reported separately.

## Audited Repository Inventory

Inventory audited on 2026-07-27 against [`.github/workflows/ci.yml`](./.github/workflows/ci.yml):

- **10 Python project entries**
- **6 Rust crates**
- **1 Terraform validation target**
- **17 CI targets in total**
- **8 tracked `smoke/run_smoke.py` pipelines**

The counts above describe the tracked repository and CI matrix. They do not include local ignored or untracked work.

## 1. Verified Measured Runs

### RAG Assistant: versioned deterministic retrieval benchmark

- **Run date:** 2026-07-27
- **Environment:** local CPU; deterministic network-free `HashEmbedder`, 512 dimensions
- **Corpus:** 10 checked-in documents, 31 chunks
- **Cases:** 40 checked-in labeled retrieval cases
- **Chunking:** 400 characters with 80-character overlap
- **Metric cutoff:** fixed recall@1 and recall@3; MRR over the first relevant source

| Metric | Baseline |
|---|---:|
| recall@1 | 0.500 |
| recall@3 | 0.775 |
| MRR | 0.629 |

| Required category | Cases | recall@1 | recall@3 | MRR |
|---|---:|---:|---:|---:|
| Direct lookup | 8 | 0.250 | 0.750 | 0.479 |
| Paraphrase | 8 | 0.625 | 0.750 | 0.688 |
| Terminology | 8 | 0.500 | 0.875 | 0.688 |
| Cross-chunk | 8 | 0.750 | 0.750 | 0.750 |
| Hard negative | 8 | 0.375 | 0.750 | 0.542 |

This result is a project regression baseline, not a leaderboard or production-quality retrieval claim. HashEmbedder is intentionally weak and deterministic. It makes CI sensitive to changes in corpus loading, chunking, labels, metric aggregation, and ranking behavior without downloading model weights.

The checked-in comparison rule rejects a change when recall@1 falls below 0.450, recall@3 falls below 0.725, MRR falls below 0.579, or any required category loses more than one of its eight top-three hits. Comparisons must keep the corpus, labels, chunk settings, and embedder fixed.

Regenerate the deterministic report:

```bash
cd ai_engineering/rag_assistant
python -m smoke.run_smoke
```

### RAG Assistant: historical five-case MiniLM re-ranking smoke run

- **Run date:** 2026-07-26
- **Environment:** CPU; `sentence-transformers` 5.6.1; `transformers` 5.14.1; `torch` 2.13.0
- **Corpus:** three checked-in sample documents at the time of the run
- **Cases:** five retrieval cases at the time of the run
- **Metric cutoff:** k = 3

| Configuration | recall@3 | MRR |
|---|---:|---:|
| Embedding retrieval | 1.000 | 0.900 |
| Cross-encoder re-ranked | 1.000 | 1.000 |
| Observed delta | +0.000 | +0.100 |

The re-ranker moved one relevant result from rank 2 to rank 1. This result predates the expanded benchmark and is retained as historical smoke evidence. It is not directly comparable with the 40-case baseline and does not establish a general quality lift.

Run the current MiniLM comparison on the expanded benchmark:

```bash
cd ai_engineering/rag_assistant
python -m smoke.run_reranker_eval
```

### Regularized Operator Zoo

- **Run date:** 2026-06-02
- **Environment:** local CPU; NumPy and Matplotlib project requirements; exact package versions were not recorded in the retained run evidence
- **Input:** `q = [1.0, 2.0, 0.5]`, `beta = 1.0`

- Maximum policy-to-gradient residual across the five operators: **1.8e-07**
- Maximum conjugate-identity difference: **2.2e-16**

The tested identities are:

```text
pi* = grad Omega*(q)
Omega*(q) = <pi*, q> - Omega(pi*)
```

Regenerate:

```bash
cd ai_engineering/rlvr/regularized_operator_zoo
python -m smoke.run_smoke
```

### GRPO Minimal

- **Run date:** 2026-06-02
- **Environment:** local CPU; NumPy and Matplotlib project requirements; exact package versions were not recorded in the retained run evidence
- **Task:** synthetic categorical verifiable-reward task
- **Protocol:** mean of 3 seeds, 1,200 steps per seed

| Method | Final accuracy |
|---|---:|
| RFT | 0.181 |
| Online RFT | 0.945 |
| GRPO+OS | 0.990 |

The measured qualitative ordering is **RFT < Online RFT < GRPO+OS**. The project targets the ordering associated with Figure 5 of Shao et al. 2024, not the paper's absolute benchmark values.

Regenerate from a shell with the sibling operator library on `PYTHONPATH`:

```bash
cd ai_engineering/rlvr/grpo_minimal
PYTHONPATH="$PYTHONPATH:$(realpath ../regularized_operator_zoo)" \
  python -m smoke.run_smoke
```

## 2. Reproducible Smoke Pipelines

These tracked projects provide a `smoke/run_smoke.py` entry point. A smoke run exercises a bounded end-to-end path; it does not automatically establish external validity or production readiness.

| Project | Command | Evidence produced |
|---|---|---|
| [RAG Assistant](./ai_engineering/rag_assistant/) | `cd ai_engineering/rag_assistant && python -m smoke.run_smoke` | Versioned 40-case deterministic retrieval benchmark with aggregate, category, and per-case metrics |
| [Agent Toolkit](./ai_engineering/agent_toolkit/) | `cd ai_engineering/agent_toolkit && python -m smoke.run_smoke` | Deterministic agent/tool execution and trace output |
| [LLM Eval Harness](./ai_engineering/llm_eval_harness/) | `cd ai_engineering/llm_eval_harness && python -m smoke.run_smoke` | Evaluation-suite execution and report generation |
| [Regularized Operator Zoo](./ai_engineering/rlvr/regularized_operator_zoo/) | `cd ai_engineering/rlvr/regularized_operator_zoo && python -m smoke.run_smoke` | Operator identity checks and beta-sweep artifacts |
| [GRPO Minimal](./ai_engineering/rlvr/grpo_minimal/) | `cd ai_engineering/rlvr/grpo_minimal && PYTHONPATH="$PYTHONPATH:$(realpath ../regularized_operator_zoo)" python -m smoke.run_smoke` | Three-method synthetic training comparison |
| [Image Captioning](./machine_learning/image_captioning_cnn_rnn_tpu/) | `cd machine_learning/image_captioning_cnn_rnn_tpu && python -m smoke.run_smoke` | CPU-compatible end-to-end captioning path |
| [Image Classification](./machine_learning/image_classification/) | `cd machine_learning/image_classification && python -m smoke.run_smoke` | Synthetic train, evaluate, persist, and inference path |
| [Predictive Maintenance](./machine_learning/predictive_maintenance/) | `cd machine_learning/predictive_maintenance && python -m smoke.run_smoke` | Synthetic telemetry, model training, persistence, and inference path |

Generated reports are local runtime artifacts unless a project README explicitly identifies a retained verified run.

## 3. Test-Suite or Validation-Only Projects

These projects are validated primarily through deterministic tests, compilation, or configuration validation rather than a separate smoke report.

### Python

| Project | CI command | Boundary |
|---|---|---|
| [NLP Text Summarization CLI](./ai_engineering/nlp_text_summarization_api/) | `cd ai_engineering/nlp_text_summarization_api && python -m unittest discover tests` | Network-free HTTP-path, persistence, concurrency, and retry tests; no retained summary-quality benchmark |

The RAG Assistant suite contains **34 tests across 6 files**, including metric aggregation, multi-source labels, missing hits, category slicing, benchmark validation, and deterministic regression thresholds.

The RAG-to-evaluation bridge is enforced separately:

```bash
cd ai_engineering/llm_eval_harness
PYTHONPATH="$PYTHONPATH:$(realpath ../rag_assistant)" \
  python -m pytest tests/test_bridge_to_rag.py -v
```

The current bridge baseline is **2 passing tests**.

### Rust

The CI matrix contains six crates:

1. [Cross-Chain Atomic Bridge](./blockchain_protocols/rust_cross_chain_atomic_bridge/)
2. [Decentralized Voting](./blockchain_protocols/rust_decentralized_voting/)
3. [Quadratic Voting and Liquid Democracy](./blockchain_protocols/rust_quadratic_voting/)
4. [PoS and ZKP Voting](./blockchain_protocols/rust_pos_zkp_voting/)
5. [PoA and ZKP Voting](./blockchain_protocols/rust_poa_zkp_voting/)
6. [DeFi Lending Protocol](./blockchain_protocols/rust_defi_lending_protocol/)

For each crate, CI runs:

```bash
cargo build --verbose
cargo test --verbose
cargo clippy --all-targets --no-deps -- -W clippy::all
```

Clippy is advisory in the current workflow. These repositories model protocol behavior in-process and do not claim deployed-chain security or consensus.

### Terraform

[SSE Coexistence Testing](./network_security/sse_coexistence_testing/) is checked with:

```bash
cd network_security/sse_coexistence_testing/terraform
terraform init -backend=false
terraform validate
```

Validation checks Terraform configuration structure. It does not deploy AWS resources or verify a live network environment.

## 4. Portable Reference Implementations

### Sales Data ETL

The [Sales Data ETL](./data_engineering/sales_data_etl_ssis/) project contains an SSIS deliverable and a Python/SQLite reference path. Linux CI verifies the portable reference, not the Windows SSIS package.

Portable execution:

```bash
cd data_engineering/sales_data_etl_ssis
python create_sales_data.py --rows 500
python python_reference_etl/sales_etl.py \
  --source sales_data.csv \
  --target sqlite:///salesdatadb.sqlite
python -m unittest discover python_reference_etl
```

This path validates the transformation, rejection, load, and logging contract without claiming that GitHub Actions executed the `.dtsx` package.

## Audit Commands

Recount the CI matrix and tracked smoke scripts from the repository root:

```bash
python - <<'PY_AUDIT'
from pathlib import Path
import re
import subprocess

ci = Path('.github/workflows/ci.yml').read_text(encoding='utf-8')
python_projects = re.findall(r'^\s*- project:\s*([^\n]+)$', ci, re.M)
rust_crates = re.findall(r'^\s*- (blockchain_protocols/[^\n]+)$', ci, re.M)
terraform_targets = len(re.findall(r'^\s*- run: terraform validate\s*$', ci, re.M))
tracked = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
smoke_scripts = sorted(path for path in tracked if path.endswith('/smoke/run_smoke.py'))

print('Python CI projects:', len(python_projects))
print('Rust CI crates:', len(rust_crates))
print('Terraform validation targets:', terraform_targets)
print('Tracked smoke scripts:', len(smoke_scripts))
for path in smoke_scripts:
    print(' ', path)
PY_AUDIT
```

The v1.1.0 release gate checked links, stale claims, whitespace, RAG tests, the RAG-to-evaluation bridge, and exact release-documentation boundaries. Issue 18 adds the versioned retrieval benchmark and its separate regression gate.
