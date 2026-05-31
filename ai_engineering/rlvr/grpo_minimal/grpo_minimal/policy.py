"""A tabular logit policy.

For each prompt we store a `vocab`-dimensional logit vector. The policy
is `pi(a | q) = softmax(logits[q])`. Gradient ascent in logit space is
all the optimization we need — there is no neural network here, by
design, because the goal is to demonstrate the algorithmic structure of
GRPO, not to scale to a real LLM.

If you wanted to scale this up to a real LM, replace `LogitPolicy` with
a thin wrapper around a transformer's token-level log-probabilities;
the rest of the training loop in `train.py` is unchanged in principle.
"""

from __future__ import annotations

import numpy as np


class LogitPolicy:
    def __init__(self, n_prompts: int, vocab: int, seed: int = 0):
        rng = np.random.default_rng(seed)
        # Small random init so the policy isn't degenerate at step 0.
        self.logits = rng.normal(scale=0.01, size=(n_prompts, vocab))

    # ---- probabilities ------------------------------------------------ #
    def log_probs(self, prompts: np.ndarray) -> np.ndarray:
        z = self.logits[prompts]
        m = np.max(z, axis=-1, keepdims=True)
        return (z - m) - np.log(np.sum(np.exp(z - m), axis=-1, keepdims=True))

    def probs(self, prompts: np.ndarray) -> np.ndarray:
        return np.exp(self.log_probs(prompts))

    def all_probs(self) -> np.ndarray:
        """Return P(action | prompt) for every prompt in the task.
        Shape: (n_prompts, vocab)."""
        all_prompts = np.arange(self.logits.shape[0])
        return self.probs(all_prompts)

    # ---- sampling ----------------------------------------------------- #
    def sample(self, prompts: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        probs = self.probs(prompts)
        # Inverse-CDF sample per row.
        cdf = np.cumsum(probs, axis=-1)
        u = rng.random(size=(probs.shape[0], 1))
        return (u < cdf).argmax(axis=-1)

    # ---- updates ------------------------------------------------------ #
    def apply_gradient(self, prompts: np.ndarray, grad_logits: np.ndarray, lr: float) -> None:
        """Add `lr * grad_logits` to the logits for the given prompts.

        `grad_logits` has the same shape as `self.logits[prompts]`. This
        is intentionally a low-level method; the methods in `methods.py`
        compute the appropriate gradient and call this.
        """
        # Aggregate by prompt (multiple samples may share a prompt).
        for i, p in enumerate(prompts):
            self.logits[p] += lr * grad_logits[i]

    def snapshot(self) -> "LogitPolicy":
        """Cheap deep copy — used to create π_old / π_ref snapshots."""
        out = LogitPolicy.__new__(LogitPolicy)
        out.logits = self.logits.copy()
        return out
