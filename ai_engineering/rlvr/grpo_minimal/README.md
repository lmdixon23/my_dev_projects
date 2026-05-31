# GRPO Minimal

## Overview

**GRPO_Minimal** is a small Python implementation of three RL post-training methods — **RFT**, **Online RFT**, and **GRPO+OS** — that all share a single training loop. The point of the project is to make Article 1's central claim of the [RLVR Operator Series](https://github.com/lmdixon23/rlvr-operator-series) concrete: these methods are *knobs on one skeleton*, not separate algorithms. The reproduction targets the qualitative ranking from **Figure 5 of Shao et al. 2024** (arXiv:2402.03300v3, page 19) on a synthetic verifiable-reward task, in under a minute of CPU time. The KL-anchor regularizer that GRPO adds to its loss is imported from `operator_zoo.losses` — that import is the load-bearing bridge between this project and the regularized-operator-zoo.

## Key Features

- **One Training Loop, Three Methods**: `train.py` takes a method callable as input. RFT, Online RFT, and GRPO+OS are each ~30 lines in `methods.py`. The *only* thing that differs between them is the `(data source, gradient coefficient)` pair — which is exactly the dimension Shao et al. Section 5.2.1 uses to unify them in Equation 5 / Table 10.
- **Load-Bearing Bridge to `operator_zoo`**: GRPO+OS imports `kl_anchor_term` from the zoo; a dedicated test (`tests/test_bridge_to_zoo.py`) confirms the import is non-decorative *and* that the Vieillard closed form holds for the advantages-as-`q` substitution.
- **Figure 5 Reproduction**: `python -m smoke.run_smoke` produces `reports/figure_5_reproduction.png` showing the three methods' accuracy curves on a synthetic categorical-bandit task. The smoke run also verifies the qualitative ranking RFT < Online RFT < GRPO+OS and writes the verdict into `reports/figure_5_reproduction.md`.
- **Synthetic but Honest Task**: A categorical bandit conditioned on a prompt, with a 0/1 verifier. The task has the structural elements GRPO actually exercises (group sampling, within-group advantage normalization, KL anchor) at the smallest possible scale.
- **Real Unit Tests**: 11+ tests across three files. The qualitative-ranking test in `test_methods.py` is the empirical analogue of Figure 5's headline claim, exercised at smoke-run scale.

## Architecture

```
grpo_minimal/
  task.py        ArithmeticVerifierTask — categorical bandit with 0/1 verifier
  policy.py      LogitPolicy — tabular logits, softmax over a small vocab
  methods.py     rft_step / online_rft_step / grpo_os_step + StepConfig
                 — imports kl_anchor_term from operator_zoo.losses
  train.py       Method-agnostic training loop + EvalConfig
tests/
  test_task_and_policy.py    simplex invariants, sampling, snapshot
  test_methods.py            each step runs; KL anchor pulls back; ranking holds
  test_bridge_to_zoo.py      the operator_zoo import is load-bearing and correct
smoke/run_smoke.py           Reproduces Figure 5 (3 curves) → reports/*.png + .md
requirements.txt             numpy, matplotlib
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Sample a group**: For each prompt, sample `G` completions from the current (or previous-iterate, or SFT) policy.
- **Score**: A deterministic verifier returns 0/1 for each completion.
- **Compute the gradient coefficient**: RFT uses 1 on filtered correct samples; GRPO+OS uses the group-normalized advantage `A_i = (R_i − mean(R)) / std(R)`.
- **Add the KL anchor (GRPO only)**: A `beta * KL(pi || pi_ref)` term is added to the loss using `kl_anchor_term` from the operator zoo.
- **Update logits**: Gradient ascent step on the per-prompt logits.
- **Repeat & evaluate**: After every `eval_every` steps, the oracle accuracy is recorded for plotting.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- No GPU, no network, no API keys. The whole smoke run finishes on a laptop CPU.
- The `regularized_operator_zoo` project (sibling directory) must be importable. Either install it or run from `ai_engineering/rlvr/` with both subdirectories on `PYTHONPATH`.

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/ai_engineering/rlvr/grpo_minimal
pip install -r requirements.txt
# Make the sibling operator_zoo importable:
export PYTHONPATH="$PYTHONPATH:$(realpath ../regularized_operator_zoo)"
```

### Running

```bash
# Reproduces Figure 5 of Shao et al. 2024 in spirit (3 curves)
python -m smoke.run_smoke
# Writes:
#   reports/figure_5_reproduction.png
#   reports/figure_5_reproduction.md
```

### Testing

```bash
python -m pytest tests/      # 11+ tests, no network required
```

## Technical Specifications

- **Language**: Python 3.10+
- **Task**: Categorical bandit conditioned on a small integer prompt; 0/1 verifier
- **Policy**: Tabular logits, per-prompt softmax over a 32-action vocabulary
- **Methods Implemented**: RFT, Online RFT, GRPO+OS (Shao et al. 2024 Table 10, rows 2/4/6)
- **KL Anchor**: `beta * KL(pi || pi_ref)`, imported from `operator_zoo.losses.kl_anchor_term`
- **Plot Backend**: Matplotlib (`Agg` headless backend, CI-safe)
- **Test Coverage**: 11+ tests; one explicitly verifies the operator-zoo bridge

## What This Project Demonstrates

- The **central claim of Article 1** of the RLVR series — that GRPO methods are knobs on one skeleton — *empirically*, in code, on a single training loop with three pluggable methods.
- A **load-bearing import** between two portfolio projects (`grpo_minimal` and `regularized_operator_zoo`) with a dedicated test that catches future "this looks unused, let's clean it up" mistakes.
- **Faithful scoping**: a synthetic task that has the structural elements of GRPO without pretending to scale to GSM8K; absolute accuracy numbers are intentionally not compared against the paper.
- **Verifier-style reward shaping** with group-normalized advantages — the exact computation Shao et al. Section 4.1.2 ("Outcome Supervision RL with GRPO") describes.

## Scope

- The task is a categorical bandit, not a sequence-generation task. **GRPO+PS (process supervision) is not implemented** because a verifiable-reward bandit doesn't naturally have per-step rewards; faking a per-step signal would be a research artifact, not a reproduction.
- The "policy" is a tabular logit array, not a neural network. Scaling to a real LM is a `LogitPolicy` -> `Transformer` swap in principle, but in practice would require a tokenizer, batching, gradient accumulation, and an attention-aware KL computation — all out of scope.
- The reference policy is a fixed snapshot of the SFT policy. The iterative GRPO of Shao et al. Algorithm 1 (where the reference is periodically refreshed) is not exercised here.
- All numerical accuracies are different from the paper's GSM8K / MATH numbers by design — the task is different. The *qualitative ranking* (RFT < Online RFT < GRPO+OS) is what the reproduction targets.

## Future Enhancements

1. **GRPO+PS (process supervision)**: Switch the task from a one-shot categorical to a small sequence-generation task (e.g., predict 3 tokens, reward intermediate correctness). That would let GRPO+PS reproduce the 4th curve of Figure 5 — the one limitation Scope calls out as deliberately deferred.
2. **Iterative GRPO**: Implement Shao et al. Algorithm 1's reference-refresh loop (the fixed-reference snapshot is the current Scope limitation) and reproduce Figure 6.
3. **PyTorch Policy**: Replace `LogitPolicy` with a small transformer over a token vocabulary; keep the rest of the loop unchanged.
4. **DAPO and MDPO**: Two more rows in the (data source, gradient coefficient) table, extending the methods set. Pin exact arXiv references at implementation time rather than citing from memory.

## References

- Shao, Z., et al. (2024). *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models.* arXiv:2402.03300.
- DeepSeek-AI. (2025). *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning.* arXiv:2501.12948.
- Schulman, J., et al. (2017). *Proximal Policy Optimization Algorithms.* arXiv:1707.06347.

## Contributing

Contributions are welcome. Open an issue first if you're planning a substantial change so we can align on scope.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
