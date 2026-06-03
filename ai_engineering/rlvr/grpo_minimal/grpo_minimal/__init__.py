"""Minimal GRPO + variants, reproducing Figure 5 of Shao et al. 2024 in spirit.

The artifact does not retrain a 1.3B model on GSM8K. It demonstrates that
**three methods (RFT, Online RFT, GRPO+OS) sit inside the unified paradigm
of Shao et al. Section 5.2.1 / Equation 5 / Table 10**, by implementing them
as different choices of (data source, gradient coefficient) on the same
training loop, and producing the qualitative ranking RFT < Online RFT <
GRPO+OS that Figure 5 reports.

The KL-anchor regularizer that GRPO adds to its loss is imported from
`operator_zoo.losses.kl_anchor_term` — that import is the real
bridge between this project and the operator zoo. The Vieillard closed
form in `operator_zoo.operators.KLToAnchor` is used in the tests as a
correctness oracle for the loss.

GRPO+PS (process supervision) is deliberately deferred. It needs a
per-step reward signal that a verifiable-reward toy task does not
naturally provide; faking one would add a research artifact that
distorts the reproduction. See README.md > Scope.
"""

from .task import ArithmeticVerifierTask
from .policy import LogitPolicy
from .methods import rft_step, online_rft_step, grpo_os_step
from .train import train, EvalConfig

__all__ = [
    "ArithmeticVerifierTask",
    "LogitPolicy",
    "rft_step", "online_rft_step", "grpo_os_step",
    "train", "EvalConfig",
]
