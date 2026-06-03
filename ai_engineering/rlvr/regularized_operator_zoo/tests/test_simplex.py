"""Every operator must return a policy on the probability simplex."""

import unittest

import numpy as np

from operator_zoo import RegularizedOp, policy_on_simplex


CASES = [
    ("entropy",          {}),
    ("kl_uniform",       {}),
    ("kl_anchor",        {}),
    ("kl_anchor",        {"anchor": np.array([0.7, 0.2, 0.1])}),
    ("tsallis",          {}),
    ("chi2",             {}),
]


class TestSimplex(unittest.TestCase):
    def test_each_operator_returns_a_valid_simplex(self):
        rng = np.random.default_rng(0)
        for name, kwargs in CASES:
            for trial in range(10):
                q = rng.normal(size=3)
                op = RegularizedOp(name, beta=0.5, **kwargs)
                pi = op.policy(q)
                self.assertTrue(
                    policy_on_simplex(pi),
                    f"{name} returned pi={pi} for q={q}",
                )

    def test_simplex_invariant_holds_across_betas(self):
        q = np.array([1.0, 2.0, 0.5])
        for beta in (0.01, 0.1, 1.0, 10.0):
            for name, kwargs in CASES:
                pi = RegularizedOp(name, beta=beta, **kwargs).policy(q)
                self.assertTrue(policy_on_simplex(pi), f"{name} beta={beta}: pi={pi}")


if __name__ == "__main__":
    unittest.main()
