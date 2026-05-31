"""Regularized greedy operators — a pedagogical zoo.

For an action-value vector q at a state and a convex regularizer Omega
on the action simplex, the *regularized greedy step* is

    Omega_star(q) = max_{pi in Delta} <pi, q> - Omega(pi)
    pi_star       = grad Omega_star(q)

This module ships concrete implementations for five named Omega:

  - NegativeEntropy             -> softmax(q / beta)
  - KLToUniform (mellowmax)     -> softmax(q / beta), same maximizer as above
                                   (mellowmax differs only in the *value* Omega_star)
  - KLToAnchor (Vieillard)      -> mu * exp(q / beta) / Z
  - Tsallis (alpha=2)           -> sparsemax (genuinely sparse policy)
  - Renyi (alpha=2)             -> a smooth interpolant

The contract every operator implements is identical:

    op = RegularizedOp("entropy", beta=1.0)
    pi = op.policy(q)        # gradient of Omega_star: the new policy
    v  = op.value(q)         # Omega_star(q): the regularized value
    om = op.omega(pi)        # the penalty Omega(pi) for a given pi

All policies returned are nonnegative and sum to 1 (the simplex
invariant). All values satisfy the conjugate identity

    Omega_star(q) == <pi_star, q> - Omega(pi_star)

This identity is the one a reader of Article 1 §3 wants to *see*; the
tests in tests/test_conjugate_identity.py verify it numerically for
each operator.

Article references (RLVR Operator Series):
  - A1 §3   Geist regularized greedy operator
  - A3      Vieillard's KL-anchored variant
  - A7      Foundations under the skeleton (MaxEnt, control as inference)
"""

from .core import RegularizedOp, policy_on_simplex
from .losses import entropy_term, kl_anchor_term
from .operators import (
    NegativeEntropy,
    KLToUniform,
    KLToAnchor,
    Tsallis,
    Renyi,
    OmegaBase,
)

__all__ = [
    "kl_anchor_term",
    "entropy_term",
    "RegularizedOp",
    "policy_on_simplex",
    "NegativeEntropy",
    "KLToUniform",
    "KLToAnchor",
    "Tsallis",
    "Renyi",
    "OmegaBase",
]
