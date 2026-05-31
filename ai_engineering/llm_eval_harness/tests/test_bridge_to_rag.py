"""Cross-project bridge test: the eval harness can grade the RAG assistant.

This test is the analogue of `grpo_minimal/tests/test_bridge_to_zoo.py` —
it catches the failure mode where two portfolio projects drift apart over
time. Specifically: if either `rag_assistant.pipeline.AskResult` or the
eval harness's `Runner(respond_fn=...)` contract changes shape, this test
breaks before users do.

The test does not call OpenAI. It builds a RAG pipeline with the
`HashEmbedder` (deterministic, no model download) and grades its outputs
with `ExactMatchEvaluator` + `RegexEvaluator` (no LLM judge).
"""

import os
import sys
import unittest

# Make the sibling project importable.
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rag_assistant")),
)
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)


def _try_import_rag():
    try:
        from rag.chunker import Chunker, Document
        from rag.embedder import HashEmbedder
        from rag.pipeline import RAGPipeline
        from rag.vector_store import VectorStore
        return Chunker, Document, HashEmbedder, RAGPipeline, VectorStore
    except ImportError:
        return None


class TestRagAssistantIsGradeableByEvalHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rag_imports = _try_import_rag()

    def setUp(self):
        if self.rag_imports is None:
            self.skipTest("rag_assistant project not importable (sibling project missing)")

    def test_eval_harness_grades_rag_outputs(self):
        Chunker, Document, HashEmbedder, RAGPipeline, VectorStore = self.rag_imports

        # Build a RAG pipeline backed by the network-free HashEmbedder.
        emb = HashEmbedder(dim=64)
        store = VectorStore(dim=emb.dim)
        pipeline = RAGPipeline(
            embedder=emb,
            store=store,
            generator=None,  # No OpenAI call; ask() returns retrieved chunks only.
            chunker=Chunker(chunk_size=120, chunk_overlap=20),
        )
        pipeline.ingest([
            Document(source="cats.md", text="Cats are small domesticated carnivores. They purr."),
            Document(source="dogs.md", text="Dogs are loyal pack animals related to wolves."),
        ])

        # Wrap RAG as a respond_fn the eval harness understands.
        def respond_fn(prompt: str) -> str:
            return pipeline.ask(prompt, k=2).answer

        # Now use the harness.
        from evals.cases import Case
        from evals.evaluators import ExactMatchEvaluator, RegexEvaluator
        from evals.runner import Runner

        cases = [
            Case(
                id="rag_returns_no_generator_message",
                prompt="anything",
                expected_regex="no generator",  # ask() without a generator returns this canonical string
            ),
        ]
        run = Runner(respond_fn=respond_fn, evaluators=[RegexEvaluator()]).run(
            suite_name="bridge_rag_to_eval", cases=cases
        )

        # The contract: the harness produced one result per case per evaluator.
        self.assertEqual(run.total(), len(cases))
        # The contract: PASS (the regex actually matched the canonical message).
        self.assertEqual(run.passed(), len(cases))

    def test_eval_harness_detects_when_rag_returns_unrelated_content(self):
        Chunker, Document, HashEmbedder, RAGPipeline, VectorStore = self.rag_imports

        emb = HashEmbedder(dim=64)
        store = VectorStore(dim=emb.dim)
        pipeline = RAGPipeline(embedder=emb, store=store, generator=None)
        pipeline.ingest([Document(source="x.md", text="some content")])

        from evals.cases import Case
        from evals.evaluators import ExactMatchEvaluator
        from evals.runner import Runner

        # Negative test: declare we expect "Paris", confirm the harness flags the mismatch.
        cases = [Case(id="negative", prompt="?", expected="Paris")]
        run = Runner(
            respond_fn=lambda p: pipeline.ask(p, k=1).answer,
            evaluators=[ExactMatchEvaluator()],
        ).run("bridge_rag_to_eval_negative", cases)
        self.assertEqual(run.passed(), 0)
        self.assertEqual(run.total(), 1)


if __name__ == "__main__":
    unittest.main()
