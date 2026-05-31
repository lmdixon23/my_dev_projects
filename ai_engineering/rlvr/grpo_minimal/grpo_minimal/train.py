"""Method-agnostic training loop.

`train(method, task, steps, ...)` runs `steps` policy updates with the
given method function (one of `rft_step`, `online_rft_step`,
`grpo_os_step` from `methods.py`) and records the oracle accuracy at
intervals. The returned history is what `smoke/run_smoke.py` then
plots as the y-axis of the Figure-5 reproduction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

import numpy as np

from .methods import StepConfig
from .policy import LogitPolicy
from .task import ArithmeticVerifierTask


@dataclass
class EvalConfig:
    eval_every: int = 50
    seed: int = 0
    step: StepConfig = field(default_factory=StepConfig)


def train(
    method: Callable,
    task: ArithmeticVerifierTask,
    sft_policy: LogitPolicy,
    n_steps: int,
    cfg: EvalConfig,
) -> tuple[LogitPolicy, np.ndarray, np.ndarray]:
    """Train `policy` (initialized from `sft_policy`) for `n_steps`.

    Returns:
        policy           the trained policy
        eval_steps       array of step indices at which eval was recorded
        eval_accuracies  array of oracle accuracies at those steps
    """
    rng = np.random.default_rng(cfg.seed)

    # Initialize current policy from SFT. ref_policy is a fixed snapshot
    # used by GRPO as the KL anchor.
    policy = sft_policy.snapshot()
    ref_policy = sft_policy.snapshot()

    accuracies: List[float] = []
    steps_recorded: List[int] = []

    for step in range(n_steps):
        prompt = int(rng.integers(0, task.n_prompts))
        method(policy, sft_policy if method.__name__ == "rft_step" else ref_policy,
               task, prompt, cfg.step, rng)

        if step % cfg.eval_every == 0:
            accuracies.append(task.oracle_accuracy(policy.all_probs()))
            steps_recorded.append(step)

    # Final eval after the last step.
    accuracies.append(task.oracle_accuracy(policy.all_probs()))
    steps_recorded.append(n_steps)

    return policy, np.asarray(steps_recorded), np.asarray(accuracies)
