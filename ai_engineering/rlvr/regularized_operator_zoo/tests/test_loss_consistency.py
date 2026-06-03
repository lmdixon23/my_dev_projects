"""Loss-side equals closed-form, in the limit.

This is the test that ties this zoo to `grpo_minimal`:
when gradient ascent on `<pi, q> - kl_anchor_term(log_pi, log_mu, beta)`
converges, the resulting `pi` must equal `KLToAnchor(lambda_kl=beta,
anchor=mu).policy(q)` — the Vieillard closed form.

If this test fails, then either:
  (a) the closed form in `operators.py` is wrong (a bug in the zoo), or
  (b) the loss in `losses.py` is computing something other than
      `beta * KL(pi || mu)` (a bug in the bridge),
or both. Either way, `grpo_minimal` would inherit the discrepancy.
"""

import unittest

import numpy as np

from operator_zoo import KLToAnchor, NegativeEntropy
from operator_zoo.losses import entropy_term, kl_anchor_term


def _log_softmax(x: np.ndarray) -> np.ndarray:
    m = np.max(x)
    return (x - m) - np.log(np.sum(np.exp(x - m)))


def _gradient_ascent_logits(q, log_mu, beta, *, kind, iters=2000, lr=0.05):
    """Maximize `<pi, q> - <regularizer>` in logit space, return the
    converged log-policy.

    Parameterization: pi = softmax(logits). We do simple gradient ascent;
    no momentum, no schedule, deliberately bare to keep the test honest
    about what we're showing.
    """
    logits = np.zeros_like(q)
    for _ in range(iters):
        log_pi = _log_softmax(logits)
        pi = np.exp(log_pi)

        # d/d logits [ <pi, q> ] = pi * (q - <pi, q>)
        score_grad = pi * (q - float(np.dot(pi, q)))

        # d/d logits [ kl_anchor_term ] when log_mu is fixed:
        #     beta * (log_pi - log_mu) + beta * 1   summed weighted by ∂pi/∂logits
        # In logit-space: d/d logits [ beta * sum pi * (log_pi - log_mu) ]
        # = beta * pi * ((log_pi - log_mu) - <pi, (log_pi - log_mu)>)
        if kind == "kl_anchor":
            diff = log_pi - log_mu
            reg_grad = beta * pi * (diff - float(np.dot(pi, diff)))
        elif kind == "entropy":
            # d/d logits [ beta * sum pi * log_pi ]
            # = beta * pi * (log_pi - <pi, log_pi>)
            reg_grad = beta * pi * (log_pi - float(np.dot(pi, log_pi)))
        else:
            raise ValueError(kind)

        logits = logits + lr * (score_grad - reg_grad)
    return _log_softmax(logits)


class TestKLAnchorLossMatchesClosedForm(unittest.TestCase):
    """Gradient ascent on the KL-anchored loss converges to the Vieillard
    closed form."""

    def test_uniform_anchor(self):
        q = np.array([1.0, 2.0, 0.5])
        mu = np.full_like(q, 1.0 / q.size)
        beta = 1.0

        log_pi_gd = _gradient_ascent_logits(q, np.log(mu), beta, kind="kl_anchor")
        pi_gd = np.exp(log_pi_gd)
        pi_closed = KLToAnchor(lambda_kl=beta, anchor=mu).policy(q)
        np.testing.assert_allclose(pi_gd, pi_closed, atol=2e-3)

    def test_non_uniform_anchor(self):
        q = np.array([1.5, 0.0, -0.5, 2.0])
        mu = np.array([0.4, 0.3, 0.2, 0.1])
        beta = 0.7

        log_pi_gd = _gradient_ascent_logits(q, np.log(mu), beta, kind="kl_anchor")
        pi_gd = np.exp(log_pi_gd)
        pi_closed = KLToAnchor(lambda_kl=beta, anchor=mu).policy(q)
        np.testing.assert_allclose(pi_gd, pi_closed, atol=3e-3)

    def test_loss_term_is_zero_when_current_equals_anchor(self):
        log_mu = np.log(np.array([0.5, 0.3, 0.2]))
        # log_pi == log_mu -> KL == 0
        self.assertAlmostEqual(kl_anchor_term(log_mu, log_mu, beta=1.0), 0.0, places=10)


class TestEntropyLossMatchesClosedForm(unittest.TestCase):
    def test_softmax_recovered(self):
        q = np.array([1.0, 2.0, 0.5])
        beta = 1.0
        log_mu_uniform = np.full_like(q, -np.log(q.size))

        log_pi_gd = _gradient_ascent_logits(q, log_mu_uniform, beta, kind="entropy")
        pi_gd = np.exp(log_pi_gd)
        pi_closed = NegativeEntropy(tau=beta).policy(q)
        np.testing.assert_allclose(pi_gd, pi_closed, atol=2e-3)


class TestAliasParityOnLossSide(unittest.TestCase):
    def test_kl_anchor_term_accepts_lambda_kl_alias(self):
        log_pi = np.log(np.array([0.5, 0.3, 0.2]))
        log_mu = np.log(np.array([0.6, 0.3, 0.1]))
        a = kl_anchor_term(log_pi, log_mu, beta=1.5)
        b = kl_anchor_term(log_pi, log_mu, lambda_kl=1.5)
        self.assertAlmostEqual(a, b, places=12)

    def test_entropy_term_accepts_tau_alias(self):
        log_pi = np.log(np.array([0.5, 0.3, 0.2]))
        a = entropy_term(log_pi, beta=2.0)
        b = entropy_term(log_pi, tau=2.0)
        self.assertAlmostEqual(a, b, places=12)


if __name__ == "__main__":
    unittest.main()
