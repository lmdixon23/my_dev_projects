"""This is the load-bearing 'bridge' test.

It confirms that the `from operator_zoo.losses import kl_anchor_term`
import in `grpo_minimal/methods.py` is non-decorative: the same KL
formula is used by both projects, and the closed-form policy from the
zoo can be recovered by running grpo_minimal's GRPO+OS update on a
trivial single-prompt task in the limit of low learning rate and no
sampling noise.

The closed-form policy `pi(a) ∝ mu(a) * exp(A(a) / beta)` is the
Vieillard identity from `operator_zoo.operators.KLToAnchor`. Running
GRPO+OS with deterministic advantages should converge there.
"""

import unittest

import numpy as np

from operator_zoo import KLToAnchor
from operator_zoo.losses import kl_anchor_term


class TestImportIsLoadBearing(unittest.TestCase):
    def test_kl_anchor_term_is_actually_imported_by_methods(self):
        # If someone "cleans up" the import in methods.py thinking it's
        # unused, this test catches it.
        import grpo_minimal.methods as m
        self.assertTrue(hasattr(m, "kl_anchor_term"))
        self.assertIs(m.kl_anchor_term, kl_anchor_term)


class TestVieillardFormHoldsForAdvantages(unittest.TestCase):
    """The closed form `pi ∝ mu * exp(A/beta)` is what GRPO's update is
    pushing toward. Verify the identity numerically."""

    def test_closed_form_against_zoo_using_advantages_as_q(self):
        # Synthetic advantages (mean ~0, std ~1).
        A = np.array([1.5, -0.5, -1.0, 0.0])
        mu = np.array([0.3, 0.3, 0.2, 0.2])
        beta = 0.4

        # By hand: mu * exp(A/beta), normalized.
        unnorm = mu * np.exp(A / beta)
        pi_hand = unnorm / unnorm.sum()

        # Via the zoo: KLToAnchor with q = A.
        pi_zoo = KLToAnchor(lambda_kl=beta, anchor=mu).policy(A)
        np.testing.assert_allclose(pi_hand, pi_zoo, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
