"""End-to-end tests using HashEmbedder so no model download / network is required."""

import os
import tempfile
import unittest

from rag.chunker import Chunker, Document
from rag.embedder import HashEmbedder
from rag.eval import EvalCase, eval_retrieval
from rag.pipeline import RAGPipeline
from rag.retriever import Retriever
from rag.vector_store import VectorStore


def make_pipeline(dim: int = 128) -> RAGPipeline:
    emb = HashEmbedder(dim=dim)
    store = VectorStore(dim=dim)
    # No generator -> ask() returns retrieval results without calling OpenAI.
    return RAGPipeline(embedder=emb, store=store, chunker=Chunker(chunk_size=120, chunk_overlap=20))


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = make_pipeline()
        self.docs = [
            Document(source="cats.md",  text="Cats are small domesticated carnivores. They purr."),
            Document(source="dogs.md",  text="Dogs are loyal pack animals descended from wolves."),
            Document(source="birds.md", text="Birds have feathers and most of them can fly."),
        ]
        self.pipeline.ingest(self.docs)

    def test_ingest_produces_chunks(self):
        self.assertGreaterEqual(len(self.pipeline.store), 3)

    def test_retrieval_returns_top_k_in_descending_score_order(self):
        retrieved = self.pipeline.retriever.retrieve("Tell me about dogs", k=3)
        self.assertEqual(len(retrieved), 3)
        scores = [r.score for r in retrieved]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_ask_without_generator_returns_no_generator_message(self):
        result = self.pipeline.ask("dogs?", k=2)
        self.assertIn("no generator", result.answer)
        self.assertEqual(len(result.retrieved), 2)


class TestVectorStoreRoundtrip(unittest.TestCase):
    def test_save_then_load_recovers_chunks_and_dim(self):
        pipeline = make_pipeline()
        pipeline.ingest([Document(source="x.md", text="abc def ghi jkl mno")])
        with tempfile.TemporaryDirectory() as tmp:
            pipeline.save(tmp)
            loaded = VectorStore.load(tmp)
            self.assertEqual(loaded.dim, pipeline.store.dim)
            self.assertEqual(len(loaded), len(pipeline.store))


class TestEval(unittest.TestCase):
    def test_eval_metrics_are_in_range(self):
        pipeline = make_pipeline()
        pipeline.ingest([
            Document(source="cats.md",  text="Cats purr and are domestic carnivores."),
            Document(source="dogs.md",  text="Dogs are loyal pack animals related to wolves."),
            Document(source="birds.md", text="Birds have feathers and lay eggs."),
        ])
        retriever = Retriever(pipeline.embedder, pipeline.store)
        result = eval_retrieval(
            retriever,
            [
                EvalCase(question="purring carnivore", relevant_sources=["cats.md"]),
                EvalCase(question="loyal pack animal", relevant_sources=["dogs.md"]),
            ],
            k=3,
        )
        self.assertEqual(result.n_cases, 2)
        self.assertGreaterEqual(result.recall_at_k, 0.0)
        self.assertLessEqual(result.recall_at_k, 1.0)


if __name__ == "__main__":
    unittest.main()
