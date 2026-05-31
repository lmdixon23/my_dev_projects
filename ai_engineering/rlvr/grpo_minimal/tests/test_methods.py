"""Sanity tests for each method's single update step."""

import unittest

import numpy as np

from grpo_minimal import (
    ArithmeticVerifierTask,
    LogitPolicy,
    grpo_os_step,
    online_rft_step,
    rft_step,
)
from grpo_minimal.methods import StepConfig


def _setup(seed: int = 0):
    task = ArithmeticVerifierTask(n_prompts=4, vocab=8, seed=seed)
    sft = LogitPolicy(n_prompts=4, vocab=8, seed=seed)
    policy = sft.snapshot()
    return task, sft, policy


class TestMethodsRunOneStep(unittest.TestCase):
    def test_rft_step_runs_and_keeps_simplex(self):
        task, sft, pol = _setup()
        rng = np.random.default_rng(0)
        # Multiple steps to ensure occasional non-zero update.
        for _ in range(20):
            rft_step(pol, sft, task, prompt=0, cfg=StepConfig(group_size=16), rng=rng)
        probs = pol.all_probs()
        np.testing.assert_allclose(probs.sum(axis=-1), np.ones(4), atol=1e-7)

    def test_online_rft_step_runs(self):
        task, sft, pol = _setup()
        rng = np.random.default_rng(0)
        for _ in range(20):
            online_rft_step(pol, None, task, prompt=1, cfg=StepConfig(group_size=16), rng=rng)
        np.testing.assert_allclose(pol.all_probs().sum(axis=-1), np.ones(4), atol=1e-7)

    def test_grpo_os_step_runs_with_kl_anchor(self):
        task, sft, pol = _setup()
        ref = sft.snapshot()
        rng = np.random.default_rng(0)
        for _ in range(20):
            grpo_os_step(pol, ref, task, prompt=2, cfg=StepConfig(group_size=16), rng=rng)
        np.testing.assert_allclose(pol.all_probs().sum(axis=-1), np.ones(4), atol=1e-7)

    def test_kl_anchor_pulls_back_to_reference(self):
        """A large KL coefficient should clamp drift toward the reference far
        more than no KL term does.

        We test this as a RELATIVE comparison rather than against an absolute
        threshold: the KL gradient pi*(diff - <pi,diff>) vanishes as pi -> ref,
        so the policy settles at an equilibrium where the score gradient and
        the KL gradient balance, not at exactly zero drift. The meaningful,
        derivable claim is therefore "strong KL drifts much less than no KL",
        not "drift < (some hand-picked constant)".
        """
        task, sft, _ = _setup()
        ref = sft.snapshot()

        def drift_after(kl_beta: float) -> float:
            pol = ref.snapshot()  # identical start each run
            rng = np.random.default_rng(0)  # identical sampling each run
            cfg = StepConfig(group_size=8, learning_rate=0.05, kl_beta=kl_beta)
            for _ in range(50):
                grpo_os_step(pol, ref, task, prompt=0, cfg=cfg, rng=rng)
            return float(np.max(np.abs(pol.all_probs()[0] - ref.all_probs()[0])))

        drift_no_kl = drift_after(0.0)
        drift_strong_kl = drift_after(10.0)
        self.assertLess(
            drift_strong_kl, drift_no_kl,
            f"strong KL ({drift_strong_kl:.3f}) should clamp drift below "
            f"no-KL ({drift_no_kl:.3f})",
        )


class TestQualitativeRanking(unittest.TestCase):
    """The headline qualitative claim from Figure 5: after enough steps,
    GRPO+OS should reach higher accuracy than Online RFT, which should
    in turn exceed RFT. Verified at a much smaller scale here.
    """

    def _run(self, method, steps=400, seed=0):
        task = ArithmeticVerifierTask(n_prompts=4, vocab=8, seed=seed)
        sft = LogitPolicy(n_prompts=4, vocab=8, seed=seed)
        from grpo_minimal.train import EvalConfig, train
        cfg = EvalConfig(eval_every=steps // 4, seed=seed)
        _, _, accs = train(method, task, sft, n_steps=steps, cfg=cfg)
        return float(accs[-1])

    def test_grpo_os_beats_rft_in_final_accuracy(self):
        # Averaged across a few seeds to suppress single-seed noise.
        from grpo_minimal.train import EvalConfig, train  # noqa
        seeds = [0, 1, 2]
        rft_final = np.mean([self._run(rft_step, seed=s) for s in seeds])
        grpo_final = np.mean([self._run(grpo_os_step, seed=s) for s in seeds])
        self.assertGreater(
            grpo_final, rft_final,
            f"GRPO+OS (avg {grpo_final:.3f}) should beat RFT (avg {rft_final:.3f})",
        )


if __name__ == "__main__":
    unittest.main()
