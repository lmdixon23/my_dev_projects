# Regularized Operator Zoo

## Overview

**Regularized_Operator_Zoo** is a small, pedagogical Python library that implements the regularized greedy operators at the heart of modern RL post-training methods. For an action-value vector `q` and a convex regularizer `Ω` on the action simplex, the *regularized greedy step* is `Ω*(q) = max_π <π, q> − Ω(π)` and the resulting policy is `π* = ∇Ω*(q)`. This library ships concrete implementations for five named `Ω` — negative entropy, KL-to-uniform (mellowmax), KL-to-anchor (Vieillard), Tsallis (sparsemax), and Rényi — with a unified API, a numerical conjugate-identity test for each, and a one-command smoke run that produces a comparison plot suitable for embedding in articles or talks.

## Key Features

- **Five Concrete Operators**: Negative entropy, KL-to-uniform, KL-to-anchor with a configurable `μ`, Tsallis (`α=2` → sparsemax), and Rényi (`α=2`).
- **Unified API**: `RegularizedOp(omega, beta=...).policy(q)` returns the maximizer; `.value(q)` returns `Ω*(q)`; `.omega(π)` returns `Ω(π)`.
- **Conjugate-Identity Test Per Operator**: Every operator is verified numerically against `Ω*(q) == ⟨π*, q⟩ − Ω(π*)` — the identity Article 1 §3 turns on.
- **Closed Forms Where They Exist**: Entropy / KL-uniform → softmax; KL-anchor → Vieillard's `μ ⋅ exp(q/β)/Z`; Tsallis → projection-onto-the-simplex (sparsemax). Rényi uses a small projected-gradient solver with a looser tolerance flagged in the tests.
- **Beta-Sweep Plot**: `python -m smoke.run_smoke` sweeps `β` from `0.01` to `100` for each operator on a fixed `q` and writes `reports/policy_vs_beta.png`. The figure that "small β → greedy on argmax, large β → anchor" claim is supposed to show.
- **Numerical Stability**: Softmax / log-sum-exp use the standard max-subtraction trick; KL-to-anchor uses `log μ + q/β` in log space before exponentiating.

## Architecture

```
operator_zoo/
  __init__.py           Public exports + RegularizedOp docstring
  core.py               RegularizedOp dispatcher + policy_on_simplex helper
  operators.py          OmegaBase + 5 concrete subclasses + project_to_simplex
tests/
  test_simplex.py             Every operator returns a valid probability simplex
  test_conjugate_identity.py  Numerical verification of Ω*(q) = ⟨π, q⟩ − Ω(π)
                              and of Vieillard's exact closed form
smoke/run_smoke.py      Beta-sweep plot + identity check, writes reports/
requirements.txt        numpy, matplotlib
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Construct**: Pick a regularizer by name (`"entropy"`, `"kl_anchor"`, `"tsallis"`, etc.) and a strength `β`.
- **Apply**: `op.policy(q)` returns the policy `π*` that maximizes `⟨π, q⟩ − Ω(π)`.
- **Inspect**: `op.value(q)` returns `Ω*(q)`; `op.omega(π)` returns the penalty at a given policy. The two together satisfy the conjugate identity that defines the operator.
- **Sweep**: `python -m smoke.run_smoke` traces how `π*` changes with `β` and writes the figure.

```python
import numpy as np
from operator_zoo import RegularizedOp

q = np.array([1.0, 2.0, 0.5])

entropy = RegularizedOp("entropy", beta=1.0)
print(entropy.policy(q))            # [0.260, 0.706, 0.034] — soft greedy

vieillard = RegularizedOp("kl_anchor", beta=1.0,
                          anchor=np.array([0.6, 0.3, 0.1]))
print(vieillard.policy(q))          # μ-tilted exponential of q/β

sparse = RegularizedOp("tsallis", beta=1.0)
print(sparse.policy(q))             # exactly zero on the smallest action
```

## Notation map

The series bible uses several symbols for what the code calls `beta`. The operators accept the bible-aligned aliases as keyword arguments — they construct the same object, but let you write in the symbol your article is using.

| Code keyword | Bible symbol | Meaning | Primary source | Used in operators |
|---|---|---|---|---|
| `beta` | β | Single regularization strength — Article 1's unifying symbol | RLVR Series A1 §3 | all operators |
| `tau`  | τ | Entropy coefficient | Geist, Scherrer, Pietquin (2019) | `NegativeEntropy`, `KLToUniform` |
| `lambda_kl` | λ | KL coefficient (Vieillard anchor) | Vieillard et al. (2020) | `KLToAnchor` |

The `_kl` suffix on `lambda_kl` is deliberate. The series bible warns:

> *The λ collision is the worst: Vieillard's KL coefficient λ and GRPO-lambda's trace parameter λ are unrelated.*

`lambda_trace` (eligibility-trace parameter) is reserved for a future GRPO-lambda operator; it does not appear on any of the operators in this zoo today.

## Operator-to-article-section map

| Code name (`omega=`) | Operator | Primary source | Series article |
|---|---|---|---|
| `"entropy"` | `Ω(π) = β·Σ π log π`; maximizer is softmax | Geist, Scherrer, Pietquin (2019), §3 | A1 §3, A7 |
| `"kl_uniform"` (mellowmax) | `Ω(π) = β·KL(π ∥ U)`; same maximizer, +log\|A\| in value | Asadi & Littman (2017) | A1 §3 |
| `"kl_anchor"` (Vieillard) | `Ω(π) = β·KL(π ∥ μ)`; maximizer is `μ·exp(q/β) / Z` | Vieillard et al. (2020) | A1 §4, A3 |
| `"tsallis"` (sparsemax) | `Ω(π) = (β/2)(Σ π² − 1)`; maximizer is sparse | Martins & Astudillo (2016); Chen, Mahajan, Hilton (2019) | A1 §3 |
| `"renyi"` | `Ω(π) = (β/2) Σ π²/μ`; solved by projected gradient | Belousov & Peters (2017) | A7 |

## The two identities, verified

The conjugate identity `Ω*(q) = ⟨π★, q⟩ − Ω(π★)` is the algebraic relation. The stronger statement is the gradient identity `π★ = ∇Ω*(q)` — the policy *is* the gradient of the regularized value. Both hold to high tolerance:

```text
∥π★ − ∇Ω*(q)∥ (finite difference, entropy, q=[1,2,0.5], β=1)  ≈  1.2e-08
Ω*(q) − (⟨π★, q⟩ − Ω(π★)) (entropy, β=1)                       ≈  0.0e+00
```

Both numbers are reproducible from `reports/smoke_report.md` after running `python -m smoke.run_smoke`. The gradient identity is what Article 1 §3 actually anchors on; the conjugate identity is what falls out of it.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- No GPU, no network, no API keys.

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/ai_engineering/rlvr/regularized_operator_zoo
pip install -r requirements.txt
```

### Running

```bash
# Smoke run + comparison plot
python -m smoke.run_smoke      # writes reports/policy_vs_beta.png and reports/smoke_report.md
```

### Testing

```bash
python -m pytest tests/        # no network, no model download
```

## Technical Specifications

- **Language**: Python 3.10+
- **Numerics**: NumPy, with a `project_to_simplex` implementation following Wang & Carreira-Perpiñán (2013)
- **Plot Backend**: Matplotlib (`Agg` backend so the smoke run is CI-headless safe)
- **Test Coverage**: 7+ tests across two files; closed-form operators verified to `1e-9`, Rényi to `1e-3` (solver tolerance is intentionally loose)
- **Article References**: A1 §3 (Geist 2019), A3 (Vieillard et al. 2020), A7 (control as inference foundations) of the RLVR Operator Series

## What This Project Demonstrates

- Working understanding of the **convex-analytic core** of modern RL post-training — the conjugate-identity-as-a-test pattern is the most direct way to show "I can read Geist 2019 *and* reproduce it."
- Discipline around **closed-form-where-available, solver-with-honest-tolerance-otherwise**: the test file makes that distinction explicit instead of hiding it.
- **Numerical stability done right**: the KL-anchor implementation works in log space; softmax uses max-subtraction; the simplex projection uses the sort-based algorithm with a clean proof.
- A **single-file plot** (`policy_vs_beta.png`) that demonstrates the qualitative claim ("small β concentrates on the max action; large β returns toward the anchor") in a form that can be linked from the article series.
- A **lightweight, dependency-free** library — numpy and matplotlib only — easy to import into a notebook, a paper, or a teaching slide deck.

## Scope

- This is a pedagogical zoo, not a production RL library. The Rényi operator uses a projected-gradient solver with a fixed step size (200 iterations by default; the tests and smoke run use 500 for tighter convergence); it converges, but slowly compared with a proper interior-point solver.
- The "action simplex" here is over a small discrete action set (3-10 actions). For large vocabularies (e.g. LLM token distributions) you'd want the same identities but a sparse / batched implementation.
- The KL-anchor operator's closed form requires the anchor to be nonzero everywhere; the implementation clips to `EPS = 1e-12` to handle the boundary safely.
- No connection to a learned `q` function — `q` here is a hand-set vector, not the output of a value network.

## Future Enhancements

1. **Stochastic-Simplex Operator**: A version that operates over distributions of `q` rather than a single point, matching Article 2's Gaussian toy. Promoted because it is the direct bridge to the RLVR-Operator-Series essay project.
2. **Streamlit Demo**: Interactive sliders over `β`, the regularizer choice, and `μ`, with the simplex visualized as a 2-simplex triangle.
3. **Tsallis-α General**: Extend the Tsallis operator beyond `α = 2` (sparsemax). Note: general `α` has **no** closed-form simplex argmax — only `α = 1` (softmax) and `α = 2` (sparsemax) do — so this reuses the iterative projected-gradient solver the Rényi operator already uses (`iters=500`), not a closed form.
4. **JAX Backend**: For batched / vectorized use across many states.

## Contributing

Contributions are welcome. Open an issue first if you're planning a substantial change so we can align on scope.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
