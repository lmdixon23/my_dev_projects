# Smoke-Pipeline Results — Index

Every project with a non-trivial runtime ships a `smoke/run_smoke.py` that exercises the code path end-to-end on synthetic or in-repo data and writes a report into the project's `reports/` directory. This index links each one.

> **Reading note:** The committed reports are *placeholder shells* with the expected structural shape (qualitative ranking, identity-check rows, expected metric ranges) but **not** filled-in numbers. The regenerate command in each report file produces the actual numbers — they're left out of source control because they drift run-to-run with random seeds. The shape of the output is what's stable. Real figures for the two flagship pipelines are recorded under **Verified runs** below.

## Verified runs (real figures, not placeholders)

The two flagship RL pipelines were run locally on **2026-06-02** — these are actual outputs. Regenerate any time with the commands in the table below.

### Regularized Operator Zoo

Both regularizer identities hold to machine precision on `q = [1.0, 2.0, 0.5], beta = 1.0`:

- **Identity 1** (gradient form, `pi* = grad Omega*(q)`): max `||pi - grad Omega*||_2` = **1.8e-07** (Tsallis); the other closed-form operators agree to ~1e-10.
- **Identity 2** (conjugate form, `Omega*(q) = <pi, q> - Omega(pi)`): max difference = **2.2e-16** across entropy, KL-to-uniform, KL-to-anchor, Tsallis, and Renyi.

### GRPO Minimal — reproduces Shao et al. 2024, Figure 5

Final accuracy on the synthetic verifiable-reward task (mean of 3 seeds, 1200 steps each):

| Method | Final accuracy |
|---|---|
| RFT | 0.181 |
| Online RFT | 0.945 |
| GRPO+OS | 0.990 |

Qualitative ranking **RFT < Online RFT < GRPO+OS** matches the paper.

## Smoke reports — regenerate locally

Each runnable project's `smoke/run_smoke.py` writes a report into its `reports/` folder. Those report files are **gitignored** (their numbers drift with random seeds), so they are not committed — run the command to produce them in a local clone. For committed, real figures see **Verified runs** above.

| Project | Regenerate command |
|---|---|
| RAG Assistant | `cd ai_engineering/rag_assistant && python -m smoke.run_smoke` |
| Agent Toolkit | `cd ai_engineering/agent_toolkit && python -m smoke.run_smoke` |
| LLM Eval Harness | `cd ai_engineering/llm_eval_harness && python -m smoke.run_smoke` |
| Regularized Operator Zoo | `cd ai_engineering/rlvr/regularized_operator_zoo && python -m smoke.run_smoke` |
| GRPO Minimal (reproduces Shao et al. 2024 Figure 5) | `cd ai_engineering/rlvr/grpo_minimal && PYTHONPATH=$PYTHONPATH:$(realpath ../regularized_operator_zoo) python -m smoke.run_smoke` |
| Image Classification | `cd machine_learning/image_classification && python -m smoke.run_smoke` |
| Image Captioning (CNN+RNN) | `cd machine_learning/image_captioning_cnn_rnn_tpu && python -m smoke.run_smoke` |
| Sentiment Analysis (BERT) | `cd machine_learning/sentiment_analysis_transfer_learning && python -m smoke.run_smoke` |
| Predictive Maintenance | `cd machine_learning/predictive_maintenance && python -m smoke.run_smoke` |
| Sales Data ETL (Python reference) | uses `create_sales_data.py` then `sales_etl.py` |

That's all 10 runnable projects — full coverage.

## Projects without a smoke pipeline

The following projects don't have a `smoke/` directory because their full test suite already exercises the code path end-to-end without external resources:

- **All five Rust blockchain projects** — `cargo test` runs the unit + integration tests on every push.
- **The Terraform SSE coexistence test** — `terraform validate` runs in the CI Terraform job; the deployment harness has its own mocked-network unit tests.
- **The ink! counter prototype** — `cargo test` covers it.

## What "placeholder report" means

Each committed `reports/*.md` (or `.html`) under the projects above contains:

- A `_Last regenerated: PLACEHOLDER_` line — clearly flags that the file has not been filled in by a real run yet.
- The exact command to regenerate it.
- The **structural shape** of the expected output — qualitative ranking, identity-check rows, expected metric ranges.

It does **not** contain absolute numerical results that would drift between runs. After you run the regenerate command, the file is overwritten with the real run's output (including a real timestamp and the actual numbers).

This pattern lets a reviewer who is browsing the repo on GitHub see *what kind of output the smoke pipeline produces* without having to run the code first. It's the "you can read about my results before installing my code" affordance.
