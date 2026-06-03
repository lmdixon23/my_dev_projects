"""Public-facing dispatcher.

`RegularizedOp("entropy", beta=1.0)` is the single import-and-use entry
point the README documents. It dispatches to the right `OmegaBase`
subclass by name.
"""

from __future__ import annotations

from typing import Dict, Type

import numpy as np

from .operators import (
    OmegaBase,
    NegativeEntropy,
    KLToUniform,
    KLToAnchor,
    Tsallis,
    Chi2,
)

_REGISTRY: Dict[str, Type[OmegaBase]] = {
    "entropy": NegativeEntropy,
    "kl_uniform": KLToUniform,
    "kl_anchor": KLToAnchor,
    "tsallis": Tsallis,
    "tsallis_sparsemax": Tsallis,
    "chi2": Chi2,
}


class RegularizedOp:
    """High-level dispatcher.

    The constructor accepts the regularizer by string name and forwards
    any remaining keyword arguments to the underlying `OmegaBase`
    subclass. That includes the bible-aligned aliases — `tau` for the
    entropy operators, `lambda_kl` for `KLToAnchor` — without the
    dispatcher having to know about them individually.

    Implementation note: `beta` defaults to `None`, not `1.0`, so that
    a caller passing only an alias (e.g. `lambda_kl=0.4`) does not
    accidentally also pass `beta=1.0` into the underlying class, which
    would trigger the bible-disciplined "pass exactly one of ..." check
    in `_resolve_beta`. The underlying class's own default (1.0) is the
    one source of truth.
    """

    def __init__(self, omega: str, beta: float | None = None, **kwargs):
        if omega not in _REGISTRY:
            raise ValueError(
                f"unknown regularizer {omega!r}; pick one of {sorted(_REGISTRY)}"
            )
        if beta is not None:
            kwargs["beta"] = beta
        self._impl: OmegaBase = _REGISTRY[omega](**kwargs)
        # `self.beta` reflects the RESOLVED value, whether the caller
        # supplied `beta`, `tau`, `lambda_kl`, or nothing.
        self.beta = self._impl.beta
        self.name = self._impl.name

    def policy(self, q: np.ndarray) -> np.ndarray:
        q = np.asarray(q, dtype=float)
        return self._impl.policy(q)

    def value(self, q: np.ndarray) -> float:
        q = np.asarray(q, dtype=float)
        return self._impl.value(q)

    def omega(self, pi: np.ndarray) -> float:
        pi = np.asarray(pi, dtype=float)
        return self._impl.omega(pi)

    def step(self, q: np.ndarray) -> np.ndarray:
        """Alias for `policy(q)` — matches the operator-style notation in
        Article 1 (the operator returns the next policy)."""
        return self.policy(q)


def policy_on_simplex(pi: np.ndarray, atol: float = 1e-6) -> bool:
    """True iff pi is nonnegative and sums to 1 within tolerance."""
    pi = np.asarray(pi, dtype=float)
    return bool(np.all(pi >= -atol) and abs(float(np.sum(pi)) - 1.0) <= atol)
