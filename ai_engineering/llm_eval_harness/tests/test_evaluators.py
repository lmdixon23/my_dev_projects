import unittest

import httpx
import numpy as np

from evals.cases import Case
from evals.evaluators import (
    EmbeddingSimilarityEvaluator,
    ExactMatchEvaluator,
    LLMJudgeEvaluator,
    RegexEvaluator,
)


def _case(**kw):
    base = {"id": "c", "prompt": "p"}
    base.update(kw)
    return Case(**base)


class TestExactMatch(unittest.TestCase):
    def test_match_after_strip_and_lower(self):
        ev = ExactMatchEvaluator()
        ok, score, _ = ev.grade(_case(expected="Paris"), " paris  ")
        self.assertTrue(ok)
        self.assertEqual(score, 1.0)

    def test_mismatch(self):
        ev = ExactMatchEvaluator()
        ok, score, _ = ev.grade(_case(expected="Paris"), "London")
        self.assertFalse(ok)
        self.assertEqual(score, 0.0)

    def test_case_sensitive_mode(self):
        ev = ExactMatchEvaluator(case_sensitive=True)
        ok, *_ = ev.grade(_case(expected="Paris"), "paris")
        self.assertFalse(ok)


class TestRegex(unittest.TestCase):
    def test_pattern_match(self):
        ok, *_ = RegexEvaluator().grade(_case(expected_regex=r"\b202[0-9]\b"), "year 2024 here")
        self.assertTrue(ok)

    def test_pattern_miss(self):
        ok, *_ = RegexEvaluator().grade(_case(expected_regex=r"\b202[0-9]\b"), "no year")
        self.assertFalse(ok)

    def test_must_not_contain(self):
        ok, *_ = RegexEvaluator().grade(_case(must_not_contain=["bad"]), "this is bad output")
        self.assertFalse(ok)


class TestEmbeddingSimilarity(unittest.TestCase):
    def test_uses_provided_embed_fn(self):
        def fake_embed(texts):
            # Two identical 4-d vectors -> cosine 1.0.
            v = np.array([1.0, 0.0, 0.0, 0.0])
            return np.stack([v, v])

        ev = EmbeddingSimilarityEvaluator(threshold=0.5, embed_fn=fake_embed)
        ok, score, _ = ev.grade(_case(expected="ref"), "candidate")
        self.assertTrue(ok)
        self.assertAlmostEqual(score, 1.0)

    def test_bag_of_words_fallback_when_no_embed_fn(self):
        # No embed_fn and no sentence-transformers -> BoW fallback path is hit
        # (or sentence-transformers is installed and produces a real score). Either way,
        # score must be in [0, 1].
        ev = EmbeddingSimilarityEvaluator(threshold=0.99, embed_fn=lambda _t: None)
        # embed_fn returning None triggers the BoW fallback inside grade().
        ok, score, _ = ev.grade(_case(expected="alpha beta gamma"), "beta gamma delta")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestLLMJudge(unittest.TestCase):
    def test_no_api_key_fails_gracefully(self):
        ev = LLMJudgeEvaluator(api_key=None)
        ok, score, detail = ev.grade(_case(expected="ref"), "candidate")
        self.assertFalse(ok)
        self.assertEqual(score, 0.0)
        self.assertIn("not set", detail)

    def test_judge_parses_score_via_mock(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "choices": [{"message": {"content": "5\nReason: it's spot on."}}],
            })
        client = httpx.Client(transport=httpx.MockTransport(handler))
        ev = LLMJudgeEvaluator(api_key="k", model="gpt-4o-mini", client=client)
        ok, score, detail = ev.grade(_case(expected="ref"), "candidate")
        self.assertTrue(ok)
        self.assertEqual(score, 1.0)
        self.assertIn("5/5", detail)

    def test_judge_clamps_out_of_range(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "choices": [{"message": {"content": "9999"}}],
            })
        client = httpx.Client(transport=httpx.MockTransport(handler))
        ev = LLMJudgeEvaluator(api_key="k", client=client)
        _, score, _ = ev.grade(_case(expected="ref"), "candidate")
        self.assertEqual(score, 1.0)  # clamps to 5/5 -> 1.0


if __name__ == "__main__":
    unittest.main()
