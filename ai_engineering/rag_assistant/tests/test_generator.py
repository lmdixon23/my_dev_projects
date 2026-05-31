"""Tests for `Generator` via httpx.MockTransport — no real OpenAI call."""

import unittest

import httpx

from rag.chunker import Chunk
from rag.generator import Generator
from rag.retriever import RetrievedChunk


def _stub_chunk(source: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        score=0.9,
        chunk=Chunk(chunk_id=f"{source}#0", doc_id=source, source=source, chunk_index=0, text=text),
    )


class TestGenerator(unittest.TestCase):
    def test_empty_retrieval_returns_no_context_answer_without_api_call(self):
        gen = Generator(api_key="anything", model="gpt-4o-mini")
        out = gen.generate("What is X?", retrieved=[])
        self.assertIn("could not find", out.answer)
        self.assertEqual(out.sources, [])
        self.assertEqual(out.tokens_used, 0)

    def test_missing_api_key_raises_when_retrieval_is_nonempty(self):
        gen = Generator(api_key=None, model="gpt-4o-mini")
        with self.assertRaises(RuntimeError):
            gen.generate("q", retrieved=[_stub_chunk("a.md", "alpha")])

    def test_happy_path_through_mock_transport(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "An answer. [source: a.md]"}}],
                    "usage": {"total_tokens": 42},
                },
            )
        client = httpx.Client(transport=httpx.MockTransport(handler))
        gen = Generator(api_key="k", model="gpt-4o-mini", client=client)
        out = gen.generate("q", retrieved=[_stub_chunk("a.md", "alpha"), _stub_chunk("b.md", "beta")])
        self.assertEqual(out.tokens_used, 42)
        self.assertEqual(out.sources, ["a.md", "b.md"])
        self.assertIn("answer", out.answer)


if __name__ == "__main__":
    unittest.main()
