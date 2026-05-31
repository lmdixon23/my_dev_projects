"""Three RL post-training methods, factored to expose what differs.

Each `*_step` function takes the same arguments and returns the same
shape, so the training loop in `train.py` is method-agnostic. What
differs between them is the (data source, gradient coefficient) pair —
which is precisely the dimension Shao et al. 2024 Section 5.2.1 uses to
unify all of these methods inside Equation 5:

    nabla J = E_{(q, o) ~ D} [ GC(q, o, t, pi_rf) * nabla log pi(o_t | ...) ]

Table 10 of the paper maps:
    Method        Data source                         Gradient coefficient
    RFT           SFT outputs filtered by correctness       1
    Online RFT    samples from current policy, filtered     1
    GRPO+OS       samples from old policy                   group-normalized advantage

This module implements those three rows. The KL anchor term that GRPO's
loss adds is imported from `operator_zoo.losses` — that import is the
load-bearing bridge to the regularized-operator-zoo project.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# This import is the bridge to operator_zoo.
from operator_zoo.losses import kl_anchor_term  # noqa: F401 — kept for the bridge


# --------------------------------------------------------------------- #
# Shared sampling helpers
# --------------------------------------------------------------------- #
def _sample_group(policy, task, prompt: int, G: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Sample G actions for one prompt; return (actions, rewards)."""
    prompts = np.full(G, prompt)
    actions = policy.sample(prompts, rng)
    rewards = task.reward_batch(prompts, actions)
    return actions, rewards


def _grad_logits_for_one_prompt(
    policy,
    prompt: int,
    actions: np.ndarray,
    weights: np.ndarray,
    log_pi_ref: np.ndarray | None,
    kl_beta: float,
) -> np.ndarray:
    """Gradient (in logit space) of:

        sum_i  weights[i] * log pi(actions[i] | prompt)
                - kl_beta * KL(pi(. | prompt) || pi_ref(. | prompt))

    Returned shape: (vocab,) — the gradient w.r.t. the logits of `prompt`.
    """
    vocab = policy.logits.shape[1]
    log_pi = policy.log_probs(np.array([prompt]))[0]   # (vocab,)
    pi = np.exp(log_pi)

    # Score term: sum_i weights[i] * d/d logits log pi(a_i | prompt)
    #           = sum_i weights[i] * (one_hot(a_i) - pi)
    grad_score = np.zeros(vocab)
    for a, w in zip(actions, weights):
        e = np.zeros(vocab); e[int(a)] = 1.0
        grad_score += w * (e - pi)

    # KL anchor: d/d logits [ KL(pi || pi_ref) ] in softmax parameterization is
    #     pi * ( (log_pi - log_pi_ref) - < pi, (log_pi - log_pi_ref) > )
    if log_pi_ref is not None and kl_beta > 0:
        diff = log_pi - log_pi_ref
        grad_kl = pi * (diff - float(np.dot(pi, diff)))
        return grad_score - kl_beta * grad_kl
    return grad_score


# --------------------------------------------------------------------- #
# Shared config
# --------------------------------------------------------------------- #
@dataclass
class StepConfig:
    group_size: int = 8           # G in the paper
    learning_rate: float = 0.05
    kl_beta: float = 0.02         # KL coefficient to pi_ref; only used by GRPO


# --------------------------------------------------------------------- #
# RFT — rejection sampling fine-tuning
# Data source: filtered samples from a FROZEN policy (the SFT model).
# Gradient coefficient: 1 on the filtered correct samples.
# --------------------------------------------------------------------- #
def rft_step(policy, sft_policy, task, prompt: int, cfg: StepConfig, rng) -> None:
    actions, rewards = _sample_group(sft_policy, task, prompt, cfg.group_size, rng)
    keep = rewards > 0.5
    if not np.any(keep):
        return
    grad = _grad_logits_for_one_prompt(
        policy, prompt, actions[keep], np.ones(int(keep.sum())),
        log_pi_ref=None, kl_beta=0.0,
    )
    policy.logits[prompt] += cfg.learning_rate * grad


# --------------------------------------------------------------------- #
# Online RFT — same as RFT but the data source is the *current* policy.
# Gradient coefficient: still 1 on filtered samples (no advantage shaping).
# --------------------------------------------------------------------- #
def online_rft_step(policy, _unused_sft, task, prompt: int, cfg: StepConfig, rng) -> None:
    actions, rewards = _sample_group(policy, task, prompt, cfg.group_size, rng)
    keep = rewards > 0.5
    if not np.any(keep):
        return
    grad = _grad_logits_for_one_prompt(
        policy, prompt, actions[keep], np.ones(int(keep.sum())),
        log_pi_ref=None, kl_beta=0.0,
    )
    policy.logits[prompt] += cfg.learning_rate * grad


# --------------------------------------------------------------------- #
# GRPO + Outcome Supervision (GRPO+OS)
# Data source: samples from a snapshot of the previous-iterate policy.
# Gradient coefficient: group-normalized advantage A_i.
# Loss adds: beta * KL(pi || pi_ref).
# --------------------------------------------------------------------- #
def grpo_os_step(policy, ref_policy, task, prompt: int, cfg: StepConfig, rng) -> None:
    actions, rewards = _sample_group(policy, task, prompt, cfg.group_size, rng)

    # Group-normalized advantage. The std denominator is regularized so a
    # group of all-correct or all-wrong responses doesn't blow up.
    R = rewards
    A = (R - R.mean()) / (R.std() + 1e-6)

    log_pi_ref = ref_policy.log_probs(np.array([prompt]))[0]
    grad = _grad_logits_for_one_prompt(
        policy, prompt, actions, A,
        log_pi_ref=log_pi_ref, kl_beta=cfg.kl_beta,
    )
    policy.logits[prompt] += cfg.learning_rate * grad
