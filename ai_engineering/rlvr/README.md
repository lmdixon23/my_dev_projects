# RLVR Companion Implementations

## Purpose

This directory contains compact, runnable companion implementations for reinforcement learning from verifiable rewards and regularized policy operators. Its purpose is to turn mathematical claims into inspectable code, tests, plots, and bounded CPU experiments.

The directory currently has two projects:

| Project | Role |
|---|---|
| [Regularized Operator Zoo](./regularized_operator_zoo/) | Implements five regularized greedy operators and numerically checks the gradient and conjugate identities that connect regularization to policy updates |
| [GRPO Minimal](./grpo_minimal/) | Places RFT, Online RFT, and GRPO+OS on one training skeleton and measures their qualitative ordering on a synthetic verifiable-reward task |

## How the Projects Connect

The projects share KL-regularization mathematics, but the current GRPO Minimal update does not call the operator-zoo loss helper during optimization. `grpo_minimal.methods` imports `kl_anchor_term` from `operator_zoo.losses` at module load, while `_grad_logits_for_one_prompt` computes the KL gradient directly.

`grpo_minimal/tests/test_bridge_to_zoo.py` checks that the imported symbol remains available and separately verifies the KL-to-anchor closed form against `KLToAnchor`. The present connection is therefore a tested mathematical and module-level bridge, not runtime delegation of the GRPO update to an operator-zoo helper.

Conceptually:

```text
regularizer and convex conjugate identities
                 |
                 v
shared KL-to-anchor formula and tested import
                 |
                 v
direct KL-gradient implementation in GRPO Minimal
```

This creates a narrow, explicit relationship between the mathematical software and the empirical post-training comparison without overstating code reuse.

## Verified Evidence

The retained measured runs are indexed in [`RESULTS.md`](../../RESULTS.md).

### Regularized Operator Zoo

Run date: 2026-06-02. For `q = [1.0, 2.0, 0.5]` and `beta = 1.0`:

- maximum policy-to-gradient residual: **1.8e-07**;
- maximum conjugate-identity difference: **2.2e-16**.

The run covers negative entropy, KL-to-uniform, KL-to-anchor, Tsallis/sparsemax, and chi-squared/Pearson regularization.

### GRPO Minimal

Run date: 2026-06-02. Mean final accuracy across three seeds and 1,200 steps:

| Method | Final accuracy |
|---|---:|
| RFT | 0.181 |
| Online RFT | 0.945 |
| GRPO+OS | 0.990 |

The result supports the qualitative ordering **RFT < Online RFT < GRPO+OS** on the repository's synthetic task. It does not reproduce the absolute GSM8K or MATH values from DeepSeekMath.

## Running the Operator Zoo

```bash
cd ai_engineering/rlvr/regularized_operator_zoo
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS or Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest tests/ -v
python -m smoke.run_smoke
```

The smoke run writes the identity report and policy-versus-beta figure under `reports/`.

## Running GRPO Minimal

### macOS or Linux

```bash
cd ai_engineering/rlvr/grpo_minimal
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export PYTHONPATH="$PYTHONPATH:$(realpath ../regularized_operator_zoo)"
python -m pytest tests/ -v
python -m smoke.run_smoke
```

### Windows PowerShell

```powershell
Set-Location ai_engineering\rlvr\grpo_minimal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path ..\regularized_operator_zoo).Path
python -m pytest tests\ -v
python -m smoke.run_smoke
```

## Relationship to the RLVR Operator Series

These projects are companion implementations for a separately managed RLVR Operator Series. The article sources, frozen review packets, publication assets, and release process remain outside `my_dev_projects`.

This separation is intentional:

- this repository contains runnable portfolio code and repository-level validation;
- the series repository owns article claims, frozen boundaries, independent review, and publication artifacts;
- changes here must not silently revise frozen article claims;
- the series source must not be absorbed into this directory.

## Scope and Limitations

- Both projects are pedagogical research implementations, not production RL training infrastructure.
- The operator zoo works on small discrete action simplexes rather than full language-model vocabularies.
- GRPO Minimal imports the operator-zoo KL helper but currently computes its update gradient directly; the bridge is mathematical and module-level rather than delegated computation.
- GRPO Minimal uses a tabular categorical policy, not a transformer.
- The synthetic task has a deterministic 0/1 verifier and does not model long-form sequence generation.
- GRPO+PS, iterative reference refresh, large-model training, distributed execution, and GPU benchmarking are not implemented.
- The retained numerical results are local CPU measurements. Exact package versions were not recorded for the 2026-06-02 runs.

## Planned Verifier Direction

A future bounded design spike will examine how verifier properties affect learning on small symbolic, mathematical, and executable-code tasks. Candidate verifier conditions include accurate, sparse, dense, noisy, biased, and exploitable reward signals.

That work is not implemented in this directory and is not part of v1.1.0. Its gate requires a discriminative CPU path, multiple seeds, reward-to-correctness diagnostics, bounded compute, and a design that does not duplicate GRPO Minimal or the separately managed Operator Series.

## References

- Geist, M., Scherrer, B., and Pietquin, O. (2019). *A Theory of Regularized Markov Decision Processes.* arXiv:1901.11275.
- Vieillard, N., et al. (2020). *Leverage the Average: an Analysis of KL Regularization in Reinforcement Learning.* arXiv:2003.14089.
- Shao, Z., et al. (2024). *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models.* arXiv:2402.03300.

Licensed under the [MIT License](../../LICENSE).
