"""A tiny verifiable-reward task.

The task is a categorical bandit conditioned on a prompt:
  - prompt  q in {0, ..., N_PROMPTS - 1}                (a small integer)
  - action  a in {0, ..., VOCAB - 1}                    (a small integer)
  - reward  r(q, a) = 1 if a == correct_action(q) else 0

The correct action is a fixed but arbitrary permutation of the prompts —
the policy has to learn the lookup table from rewards alone.

Why this shape: it has the structural elements GRPO actually exercises
(group of G completions per prompt, verifiable 0/1 reward, advantage
normalization within the group, KL anchor to a reference policy), in
the smallest possible setting that still makes the dynamics
interesting. It does NOT have multi-step reasoning structure, which is
why GRPO+PS (process supervision) is not reproducible here.
"""

from __future__ import annotations

import numpy as np


class ArithmeticVerifierTask:
    """A categorical bandit with a verifiable reward.

    The "correct action" for each prompt is fixed at construction time.
    """

    def __init__(self, n_prompts: int = 8, vocab: int = 32, seed: int = 0):
        self.n_prompts = n_prompts
        self.vocab = vocab
        rng = np.random.default_rng(seed)
        # Each prompt's correct action is a fixed integer in [0, vocab).
        # Drawing from a non-trivial subset of the vocab keeps the task
        # learnable (no two prompts map to the same answer is not required;
        # the policy can share probability mass when ambiguous).
        self._correct = rng.integers(0, vocab, size=n_prompts)

    def correct_action(self, prompt: int) -> int:
        return int(self._correct[prompt])

    def reward(self, prompt: int, action: int) -> float:
        return 1.0 if action == int(self._correct[prompt]) else 0.0

    def reward_batch(self, prompts: np.ndarray, actions: np.ndarray) -> np.ndarray:
        return (actions == self._correct[prompts]).astype(np.float32)

    def random_prompts(self, batch: int, rng: np.random.Generator) -> np.ndarray:
        return rng.integers(0, self.n_prompts, size=batch)

    def oracle_accuracy(self, policy_probs_per_prompt: np.ndarray) -> float:
        """Average probability of the correct action across prompts.
        Used as the evaluation metric — matches Figure 5's y-axis in
        spirit (accuracy on a held-out set)."""
        n = self.n_prompts
        return float(np.mean(policy_probs_per_prompt[np.arange(n), self._correct]))
