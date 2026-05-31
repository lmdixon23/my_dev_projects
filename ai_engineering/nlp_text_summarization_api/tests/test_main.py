"""Unit tests for the parts of `main` that don't require the OpenAI API.

The HTTP-calling code path is exercised by `test_summarize_one_*` using
an httpx MockTransport, so no real network or API key is needed.
"""

import os
import sqlite3
import sys
import tempfile
import unittest

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import (  # noqa: E402
    KeyRing,
    analyze_summaries,
    open_db,
    render_analysis,
    save_feedback,
    save_summary,
    summarize_one,
)


class TestKeyRing(unittest.TestCase):
    def test_rejects_empty(self):
        with self.assertRaises(RuntimeError):
            KeyRing([None, ""])

    def test_rotates_round_robin(self):
        kr = KeyRing(["a", "b"])
        first = kr.current
        kr.rotate()
        self.assertNotEqual(kr.current, first)
        kr.rotate()
        self.assertEqual(kr.current, first)


class TestPersistenceAndAnalysis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test.db")
        self.conn = open_db(self.db_path)

    def tearDown(self):
        self.conn.close()

    def _seed(self):
        save_summary(
            self.conn, model="gpt-3.5-turbo", language="en",
            tokens_used=42, original_text="a long document " * 30,
            summary="Document discusses cats, dogs, and policy reform.",
        )
        save_summary(
            self.conn, model="gpt-3.5-turbo", language="en",
            tokens_used=51, original_text="another long document",
            summary="Policy reform regarding cats and budgets.",
        )

    def test_save_and_feedback(self):
        sid = save_summary(
            self.conn, model="m", language="en", tokens_used=1,
            original_text="x", summary="y",
        )
        save_feedback(self.conn, sid, "great")
        got = self.conn.execute("SELECT feedback FROM summaries WHERE id = ?", (sid,)).fetchone()
        self.assertEqual(got[0], "great")

    def test_analysis_handles_empty_db(self):
        stats = analyze_summaries(self.conn)
        self.assertEqual(stats["count"], 0)
        self.assertIn("No summaries", render_analysis(stats))

    def test_analysis_counts_words_and_excludes_stopwords(self):
        self._seed()
        stats = analyze_summaries(self.conn)
        self.assertEqual(stats["count"], 2)
        words = dict(stats["top_words"])
        # 'cats' and 'policy' appear in both summaries.
        self.assertEqual(words.get("cats"), 2)
        self.assertEqual(words.get("policy"), 2)
        # Stopword should not appear.
        self.assertNotIn("and", words)


class TestSummarizeOneWithMockTransport(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "  short summary  "}}],
                    "usage": {"total_tokens": 99},
                },
            )
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await summarize_one(
                client, "long text",
                model="gpt-3.5-turbo", language="en",
                max_tokens=50, keys=KeyRing(["k"]),
            )
        self.assertIsNotNone(result)
        self.assertEqual(result.summary, "short summary")
        self.assertEqual(result.tokens_used, 99)

    async def test_429_triggers_retry_then_succeeds(self):
        calls = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(429, json={"error": "rate limited"})
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "ok"}}],
                    "usage": {"total_tokens": 10},
                },
            )
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            kr = KeyRing(["k1", "k2"])
            result = await summarize_one(
                client, "x", model="gpt-3.5-turbo", language="en",
                max_tokens=10, keys=kr, retries=3,
            )
        self.assertIsNotNone(result)
        self.assertEqual(calls["n"], 2)


if __name__ == "__main__":
    unittest.main()
