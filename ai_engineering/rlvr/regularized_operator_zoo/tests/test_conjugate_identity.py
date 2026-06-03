"""The conjugate identity is the heart of Article 1 §3:

    Omega_star(q) == <pi_star, q> - Omega(pi_star)

If this fails for any (omega, q) pair, the operator implementation is wrong.
"""

import unittest

import numpy as np

from operator_zoo import RegularizedOp


CLOSED_FORM_CASES = [
    # (name, kwargs, tolerance) — operators with closed-form policies
    # should match the identity to high tolerance. Chi2 uses a solver
    # and gets a looser tolerance.
    ("entropy",     {},                                   1e-9),
    ("kl_uniform",  {},                                   1e-9),
    ("kl_anchor",   {},                                   1e-9),
    ("kl_anchor",   {"anchor": np.array([0.6, 0.3, 0.1])}, 1e-9),
    ("tsallis",     {},                                   1e-9),
]


class TestConjugateIdentity(unittest.TestCase):
    def test_closed_form_operators_satisfy_identity(self):
        rng = np.random.default_rng(42)
        for name, kwargs, tol in CLOSED_FORM_CASES:
            for trial in range(20):
                q = rng.normal(size=3)
                for beta in (0.1, 1.0, 5.0):
                    op = RegularizedOp(name, beta=beta, **kwargs)
                    pi = op.policy(q)
                    rhs = float(np.dot(pi, q) - op.omega(pi))
                    lhs = op.value(q)
                    self.assertAlmostEqual(
                        lhs, rhs, delta=tol,
                        msg=f"{name} beta={beta} q={q}: lhs={lhs} rhs={rhs}",
                    )

    def test_chi2_identity_within_solver_tolerance(self):
        """Chi2 (Pearson) uses projected-gradient; identity holds approximately."""
        q = np.array([1.0, 2.0, 0.5])
        op = RegularizedOp("chi2", beta=1.0, iters=500, lr=0.1)
        pi = op.policy(q)
        rhs = float(np.dot(pi, q) - op.omega(pi))
        lhs = op.value(q)
        # Looser tolerance — solver convergence, not algebra.
        self.assertAlmostEqual(lhs, rhs, delta=1e-3)


class TestVieillardClosedForm(unittest.TestCase):
    """The KL-anchored operator's maximizer should equal
    pi_star(a) propto mu(a) * exp(q(a) / beta) exactly."""

    def test_vieillard_form(self):
        rng = np.random.default_rng(7)
        for trial in range(10):
            mu = rng.dirichlet(alpha=np.ones(4))
            q = rng.normal(size=4)
            beta = float(rng.uniform(0.1, 5.0))
            op = RegularizedOp("kl_anchor", beta=beta, anchor=mu)
            pi = op.policy(q)

            unnorm = mu * np.exp(q / beta)
            expected = unnorm / np.sum(unnorm)
            np.testing.assert_allclose(pi, expected, atol=1e-9)


class TestBetaLimits(unittest.TestCase):
    """Sanity-check limiting behaviour: tiny beta -> nearly greedy on argmax(q)."""

    def test_small_beta_concentrates_on_argmax(self):
        q = np.array([1.0, 2.0, 0.5])
        pi = RegularizedOp("entropy", beta=1e-3).policy(q)
        self.assertEqual(int(np.argmax(pi)), int(np.argmax(q)))
        self.assertGreater(pi[int(np.argmax(q))], 0.99)

    def test_large_beta_approaches_uniform(self):
        q = np.array([1.0, 2.0, 0.5])
        pi = RegularizedOp("entropy", beta=1e6).policy(q)
        np.testing.assert_allclose(pi, [1 / 3, 1 / 3, 1 / 3], atol=1e-4)


if __name__ == "__main__":
    unittest.main()
