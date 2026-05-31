"""Loss-side counterparts to the closed-form regularized operators.

The operators in `operator_zoo.operators` solve `max_pi <pi, q> - Omega(pi)`
in closed form and return the maximizer `pi* = grad Omega*(q)`. That is
the **analytic** view of the regularized greedy step — useful for proofs,
worked examples, and as a test oracle.

In practice, modern RL post-training methods (PPO, GRPO, MDPO, ...)
do not use the closed-form policy directly. Their policy is a neural
network with a softmax over a large vocabulary, and the regularizer
shows up **inside the loss** as an additive KL or entropy term that
gradient descent then minimizes. This module exposes those loss-side
counterparts:

  * `kl_anchor_term(log_pi_curr, log_pi_ref, beta)`
        Returns `beta * sum_a pi_curr(a) * (log pi_curr(a) - log pi_ref(a))`.
        This is `beta * KL(pi_curr || pi_ref)`, evaluated at the current policy.
        It is the loss-side analogue of `KLToAnchor` from `operators.py`.

  * `entropy_term(log_pi_curr, beta)`
        Returns `beta * sum_a pi_curr(a) * log pi_curr(a)` — i.e. `beta * (-H(pi))`.
        It is the loss-side analogue of `NegativeEntropy`.

The contract: when gradient ascent on `<pi(theta), q> - kl_anchor_term(log_pi(theta), log_mu, beta)`
converges, the resulting `pi(theta)` matches the closed-form policy
`KLToAnchor(lambda_kl=beta, anchor=mu).policy(q)` to within solver
tolerance. The test `tests/test_loss_consistency.py` proves this
numerically; that test is what makes the bridge from this zoo to
`grpo_minimal` non-decorative.
"""

from __future__ import annotations

import numpy as np

EPS = 1e-12


def kl_anchor_term(
    log_pi_curr: np.ndarray,
    log_pi_ref: np.ndarray,
    beta: float | None = None,
    *,
    lambda_kl: float | None = None,
) -> float:
    """`beta * KL(pi_curr || pi_ref)`, evaluated at the current policy.

    Both inputs are log-probability vectors over the same action space;
    they must each sum-exp to 1 (i.e., they are normalized).

    `lambda_kl` is an alias for `beta` matching the bible's symbol for
    Vieillard's KL coefficient. Exactly one of the two must be supplied.
    """
    coeff = _resolve_coeff(beta, lambda_kl=lambda_kl)
    pi_curr = np.exp(log_pi_curr)
    return float(coeff * np.sum(pi_curr * (log_pi_curr - log_pi_ref)))


def entropy_term(
    log_pi_curr: np.ndarray,
    beta: float | None = None,
    *,
    tau: float | None = None,
) -> float:
    """`beta * (-H(pi_curr))` — i.e. the negative-entropy penalty applied
    to the current policy, evaluated at `pi_curr = exp(log_pi_curr)`."""
    coeff = _resolve_coeff(beta, tau=tau)
    pi_curr = np.exp(log_pi_curr)
    safe = np.clip(pi_curr, EPS, 1.0)
    return float(coeff * np.sum(safe * np.log(safe)))


# --------------------------------------------------------------------- #
# Internal: one resolver shared by both loss terms.
# --------------------------------------------------------------------- #
def _resolve_coeff(beta, **aliases):
    given = {k: v for k, v in (("beta", beta), *aliases.items()) if v is not None}
    if len(given) == 0:
        return 1.0
    if len(given) > 1:
        raise ValueError(
            f"pass exactly one of {sorted(given)}; the aliases are interchangeable"
        )
    (val,) = given.values()
    return float(val)
