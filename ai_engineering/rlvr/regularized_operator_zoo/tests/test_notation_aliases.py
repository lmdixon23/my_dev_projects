"""The bible's notation aliases (`tau`, `lambda_kl`) must produce
the same operator object as the canonical `beta`.

The aliases exist so a reader who arrived from Article 3 (Vieillard's λ)
or Article 7 (MaxEnt's τ) can construct the operator with the symbol
they're holding in their head, without having to learn the zoo's
internal canonical name first.
"""

import unittest

import numpy as np

from operator_zoo import KLToAnchor, KLToUniform, NegativeEntropy, RegularizedOp


class TestAliasEquivalence(unittest.TestCase):
    def test_tau_alias_on_negative_entropy(self):
        a = NegativeEntropy(beta=0.7)
        b = NegativeEntropy(tau=0.7)
        self.assertAlmostEqual(a.beta, b.beta)
        q = np.array([1.0, 2.0, 0.5])
        np.testing.assert_allclose(a.policy(q), b.policy(q))

    def test_tau_alias_on_kl_to_uniform(self):
        a = KLToUniform(beta=2.5)
        b = KLToUniform(tau=2.5)
        self.assertAlmostEqual(a.beta, b.beta)

    def test_lambda_kl_alias_on_kl_to_anchor(self):
        mu = np.array([0.6, 0.3, 0.1])
        a = KLToAnchor(beta=0.4, anchor=mu)
        b = KLToAnchor(lambda_kl=0.4, anchor=mu)
        q = np.array([1.0, 2.0, 0.5])
        np.testing.assert_allclose(a.policy(q), b.policy(q))


class TestAliasGuardsAgainstAmbiguity(unittest.TestCase):
    def test_passing_both_beta_and_tau_raises(self):
        with self.assertRaises(ValueError):
            NegativeEntropy(beta=0.5, tau=0.5)

    def test_passing_both_beta_and_lambda_kl_raises(self):
        with self.assertRaises(ValueError):
            KLToAnchor(beta=0.5, lambda_kl=0.5)


class TestAliasDefaults(unittest.TestCase):
    def test_no_argument_uses_unit_beta(self):
        self.assertEqual(NegativeEntropy().beta, 1.0)
        self.assertEqual(KLToUniform().beta, 1.0)
        self.assertEqual(KLToAnchor().beta, 1.0)


class TestDispatcherForwardsAliasesWithoutInjectingBeta(unittest.TestCase):
    """Regression test for a dispatcher bug:

    Before the fix, `RegularizedOp("kl_anchor", lambda_kl=0.4, ...)` would
    fail because the dispatcher unconditionally injected `beta=1.0` into
    the call, and the underlying `_resolve_beta` then raised "pass
    exactly one of [beta, lambda_kl]" — a confusing error that pointed
    at the wrong layer.
    """

    def test_lambda_kl_through_dispatcher_succeeds_and_stores_resolved_beta(self):
        mu = np.array([0.6, 0.3, 0.1])
        op = RegularizedOp("kl_anchor", lambda_kl=0.4, anchor=mu)
        # No exception, AND self.beta reflects the resolved value (0.4),
        # not the dispatcher's old default of 1.0.
        self.assertAlmostEqual(op.beta, 0.4)

    def test_tau_through_dispatcher_succeeds(self):
        op = RegularizedOp("entropy", tau=2.5)
        self.assertAlmostEqual(op.beta, 2.5)

    def test_dispatcher_default_still_yields_unit_beta(self):
        # With no coefficient supplied, the underlying class's default
        # of 1.0 must propagate up to the dispatcher's self.beta.
        op = RegularizedOp("entropy")
        self.assertEqual(op.beta, 1.0)

    def test_dispatcher_with_beta_keeps_working_for_back_compat(self):
        op = RegularizedOp("entropy", beta=0.5)
        self.assertEqual(op.beta, 0.5)

    def test_dispatcher_with_both_beta_and_alias_still_raises(self):
        # The guard against double-spec must still work through the dispatcher.
        with self.assertRaises(ValueError):
            RegularizedOp("entropy", beta=0.5, tau=0.5)


if __name__ == "__main__":
    unittest.main()
