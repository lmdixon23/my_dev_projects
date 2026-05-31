import unittest

import numpy as np

from grpo_minimal import ArithmeticVerifierTask, LogitPolicy


class TestTask(unittest.TestCase):
    def test_correct_action_is_deterministic_per_seed(self):
        a = ArithmeticVerifierTask(n_prompts=8, vocab=16, seed=42)
        b = ArithmeticVerifierTask(n_prompts=8, vocab=16, seed=42)
        for p in range(8):
            self.assertEqual(a.correct_action(p), b.correct_action(p))

    def test_reward_batch_matches_per_sample(self):
        task = ArithmeticVerifierTask(n_prompts=4, vocab=8, seed=0)
        prompts = np.array([0, 1, 2, 3, 0])
        actions = np.array([task.correct_action(0), 0, task.correct_action(2), 0, 0])
        r = task.reward_batch(prompts, actions)
        for i, (p, a, ri) in enumerate(zip(prompts, actions, r)):
            self.assertEqual(ri, task.reward(int(p), int(a)))


class TestPolicy(unittest.TestCase):
    def test_probs_sum_to_one_per_prompt(self):
        pol = LogitPolicy(n_prompts=5, vocab=12, seed=0)
        probs = pol.all_probs()
        np.testing.assert_allclose(probs.sum(axis=-1), np.ones(5), atol=1e-9)

    def test_sample_returns_valid_actions(self):
        pol = LogitPolicy(n_prompts=5, vocab=12, seed=0)
        rng = np.random.default_rng(0)
        a = pol.sample(np.array([0, 1, 2]), rng)
        self.assertTrue(np.all((a >= 0) & (a < 12)))

    def test_snapshot_is_independent_copy(self):
        pol = LogitPolicy(n_prompts=3, vocab=4, seed=0)
        snap = pol.snapshot()
        pol.logits[0, 0] += 99.0
        self.assertFalse(np.array_equal(pol.logits, snap.logits))


if __name__ == "__main__":
    unittest.main()
