"""Concrete Omega implementations.

Each subclass of OmegaBase provides three primitives:

    policy(q)        -- argmax_{pi in Delta} <pi, q> - Omega(pi)
                        equivalently grad Omega_star(q)
    value(q)         -- Omega_star(q) = max_{pi in Delta} <pi, q> - Omega(pi)
    omega(pi)        -- Omega(pi), evaluated at a given policy

Where a closed-form policy is available we use it (entropy / KL-anchor /
Tsallis). Where it is not (Renyi alpha=2), we solve the convex problem
with a projected-gradient step. The solver is correct enough for
pedagogical use; it is not optimized for large action spaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

EPS = 1e-12


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _stable_softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    e = np.exp(x)
    return e / np.sum(e)


def project_to_simplex(v: np.ndarray) -> np.ndarray:
    """Euclidean projection of v onto the probability simplex.

    Reference: Wang & Carreira-Perpinan, 2013, "Projection onto the
    probability simplex: an efficient algorithm with a simple proof."
    """
    n = v.size
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - 1.0
    rho_candidates = np.where(u - cssv / (np.arange(n) + 1) > 0)[0]
    rho = rho_candidates[-1] if rho_candidates.size > 0 else n - 1
    theta = cssv[rho] / (rho + 1.0)
    return np.maximum(v - theta, 0.0)


# --------------------------------------------------------------------- #
# Base
# --------------------------------------------------------------------- #
def _resolve_beta(beta: float | None, **aliases) -> float:
    """Resolve `beta` from either the canonical keyword or a series-bible
    alias (`tau`, `lambda_kl`). Exactly one of the available names must be
    given. The bible's *Notation hazards* section motivates this:

      - `tau`        = entropy coefficient (Geist, Vieillard)
      - `lambda_kl`  = KL coefficient (Vieillard); the suffix `_kl`
                       disambiguates it from `lambda_trace` (GRPO-lambda's
                       eligibility-trace parameter), which the bible flags
                       as the worst notation collision in the series.

    The canonical attribute is still `self.beta` — the bible names `β`
    as Article 1's unifying symbol. The aliases exist so a reader who
    arrived from Article 3 (Vieillard's λ) or Article 7 (MaxEnt's τ) can
    construct the operator with the symbol they're holding in their head.
    """
    given = {name: val for name, val in (("beta", beta), *aliases.items()) if val is not None}
    if len(given) == 0:
        return 1.0  # default
    if len(given) > 1:
        raise ValueError(
            f"pass exactly one of {sorted(given)}; the aliases are "
            f"interchangeable but providing two values is ambiguous"
        )
    value, = given.values()
    return float(value)


class OmegaBase(ABC):
    name: str

    def __init__(self, beta: float | None = None):
        b = beta if beta is not None else 1.0
        if b <= 0:
            raise ValueError("beta must be > 0")
        self.beta = b

    @abstractmethod
    def policy(self, q: np.ndarray) -> np.ndarray: ...

    @abstractmethod
    def value(self, q: np.ndarray) -> float: ...

    @abstractmethod
    def omega(self, pi: np.ndarray) -> float: ...


# --------------------------------------------------------------------- #
# Negative entropy: -H(pi) = sum pi log pi
# --------------------------------------------------------------------- #
class NegativeEntropy(OmegaBase):
    name = "entropy"

    def __init__(self, beta: float | None = None, *, tau: float | None = None):
        # `tau` is the bible's symbol for the entropy coefficient (Geist, Vieillard).
        super().__init__(beta=_resolve_beta(beta, tau=tau))

    def policy(self, q: np.ndarray) -> np.ndarray:
        return _stable_softmax(q / self.beta)

    def value(self, q: np.ndarray) -> float:
        # Omega_star(q) = beta * log sum exp(q / beta), the soft maximum.
        scaled = q / self.beta
        m = np.max(scaled)
        return float(self.beta * (m + np.log(np.sum(np.exp(scaled - m)))))

    def omega(self, pi: np.ndarray) -> float:
        pi = np.clip(pi, EPS, 1.0)
        return float(self.beta * np.sum(pi * np.log(pi)))


# --------------------------------------------------------------------- #
# KL to uniform (mellowmax)
# --------------------------------------------------------------------- #
class KLToUniform(OmegaBase):
    """Omega(pi) = beta * KL(pi || uniform). The maximizer is the same
    softmax as NegativeEntropy; the *value* differs by a constant
    beta * log |A|. Useful pedagogically because it explicitly shows the
    anchor (uniform) entering the formula."""

    name = "kl_uniform"

    def __init__(self, beta: float | None = None, *, tau: float | None = None):
        # `tau` again — KL-to-uniform is the entropy operator up to a
        # constant, so the same bible alias applies.
        super().__init__(beta=_resolve_beta(beta, tau=tau))

    def policy(self, q: np.ndarray) -> np.ndarray:
        return _stable_softmax(q / self.beta)

    def value(self, q: np.ndarray) -> float:
        n = q.size
        scaled = q / self.beta
        m = np.max(scaled)
        # mellowmax (Asadi & Littman, 2017):
        return float(self.beta * (m + np.log(np.sum(np.exp(scaled - m)) / n)))

    def omega(self, pi: np.ndarray) -> float:
        n = pi.size
        pi = np.clip(pi, EPS, 1.0)
        return float(self.beta * np.sum(pi * (np.log(pi) + np.log(n))))


# --------------------------------------------------------------------- #
# KL to a general anchor mu (Vieillard et al., 2020)
# --------------------------------------------------------------------- #
class KLToAnchor(OmegaBase):
    """Omega(pi) = beta * KL(pi || mu).
    Closed-form policy: pi_star(a) propto mu(a) * exp(q(a) / beta).
    """

    name = "kl_anchor"

    def __init__(
        self,
        beta: float | None = None,
        anchor: np.ndarray | None = None,
        *,
        lambda_kl: float | None = None,
    ):
        # `lambda_kl` is the bible-aligned name for Vieillard's KL coefficient.
        # The underscore-`kl` suffix is deliberate: it disambiguates against
        # `lambda_trace` (GRPO-lambda's eligibility-trace parameter), which the
        # bible flags as the worst notation collision in the series.
        super().__init__(beta=_resolve_beta(beta, lambda_kl=lambda_kl))
        self._anchor = None if anchor is None else np.asarray(anchor, dtype=float)

    def _resolve_anchor(self, q: np.ndarray) -> np.ndarray:
        if self._anchor is None:
            return np.full_like(q, 1.0 / q.size, dtype=float)
        if self._anchor.shape != q.shape:
            raise ValueError(
                f"anchor has shape {self._anchor.shape}, q has shape {q.shape}"
            )
        return self._anchor

    def policy(self, q: np.ndarray) -> np.ndarray:
        mu = self._resolve_anchor(q)
        log_pi_unnorm = np.log(np.clip(mu, EPS, 1.0)) + q / self.beta
        # subtract max for stability before exp
        log_pi_unnorm = log_pi_unnorm - np.max(log_pi_unnorm)
        pi = np.exp(log_pi_unnorm)
        return pi / np.sum(pi)

    def value(self, q: np.ndarray) -> float:
        mu = self._resolve_anchor(q)
        scaled = q / self.beta
        m = np.max(scaled + np.log(np.clip(mu, EPS, 1.0)))
        # Omega_star(q) = beta * log sum mu_a * exp(q_a / beta)
        return float(self.beta * (m + np.log(
            np.sum(np.clip(mu, EPS, 1.0) * np.exp(scaled + np.log(np.clip(mu, EPS, 1.0)) - m))
        )))

    def omega(self, pi: np.ndarray) -> float:
        if pi.size == 0:
            return 0.0
        mu = self._resolve_anchor(pi)
        pi_c = np.clip(pi, EPS, 1.0)
        mu_c = np.clip(mu, EPS, 1.0)
        return float(self.beta * np.sum(pi_c * (np.log(pi_c) - np.log(mu_c))))


# --------------------------------------------------------------------- #
# Tsallis (alpha = 2) -> sparsemax
# --------------------------------------------------------------------- #
class Tsallis(OmegaBase):
    """Omega(pi) = (beta/2) * (sum pi^2 - 1). Maximizer is sparsemax."""

    name = "tsallis_sparsemax"

    def policy(self, q: np.ndarray) -> np.ndarray:
        # Sparsemax = projection of q / beta onto the simplex.
        return project_to_simplex(q / self.beta)

    def value(self, q: np.ndarray) -> float:
        pi = self.policy(q)
        return float(np.dot(pi, q) - self.omega(pi))

    def omega(self, pi: np.ndarray) -> float:
        return float(0.5 * self.beta * (np.sum(pi ** 2) - 1.0))


# --------------------------------------------------------------------- #
# Renyi (alpha = 2): Omega(pi) = (beta/2) * sum (pi^2 / mu)
# Solved via projected gradient since there is no clean closed form for
# the inner product version we use. Pedagogical only.
# --------------------------------------------------------------------- #
class Renyi(OmegaBase):
    name = "renyi"

    def __init__(self, beta: float = 1.0, anchor: np.ndarray | None = None,
                 iters: int = 200, lr: float = 0.1):
        super().__init__(beta)
        self._anchor = None if anchor is None else np.asarray(anchor, dtype=float)
        self.iters = iters
        self.lr = lr

    def _resolve_anchor(self, q: np.ndarray) -> np.ndarray:
        if self._anchor is None:
            return np.full_like(q, 1.0 / q.size, dtype=float)
        return self._anchor

    def policy(self, q: np.ndarray) -> np.ndarray:
        mu = np.clip(self._resolve_anchor(q), EPS, 1.0)
        pi = mu.copy()
        for _ in range(self.iters):
            grad_obj = q - self.beta * pi / mu  # d/dpi of <pi, q> - Omega(pi)
            pi = project_to_simplex(pi + self.lr * grad_obj)
        return pi

    def value(self, q: np.ndarray) -> float:
        pi = self.policy(q)
        return float(np.dot(pi, q) - self.omega(pi))

    def omega(self, pi: np.ndarray) -> float:
        mu = np.clip(self._resolve_anchor(pi), EPS, 1.0)
        return float(0.5 * self.beta * np.sum(pi ** 2 / mu))
