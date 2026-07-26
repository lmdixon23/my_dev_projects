"""Network-free tests for optional cross-encoder re-ranking."""

import unittest

from rag.chunker import Chunk, Chunker, Document
from rag.embedder import HashEmbedder
from rag.pipeline import RAGPipeline
from rag.reranker import CrossEncoderReranker
from rag.retriever import RetrievedChunk, Retriever
from rag.vector_store import VectorStore


def make_chunk(index: int, source: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"doc#{index}",
        doc_id="doc",
        source=source,
        chunk_index=index,
        text=text,
    )


class FakeCrossEncoder:
    def __init__(self, scores):
        self.scores = scores
        self.calls = []

    def predict(self, pairs, *, batch_size, show_progress_bar):
        self.calls.append(
            {
                "pairs": list(pairs),
                "batch_size": batch_size,
                "show_progress_bar": show_progress_bar,
            }
        )
        return self.scores[: len(pairs)]


class FakeEmbedder:
    dim = 2

    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


class FakeStore:
    dim = 2

    def __init__(self, chunks):
        self.chunks = chunks
        self.requested_k = None

    def search(self, query_vector, k):
        self.requested_k = k
        scores = [0.9, 0.8, 0.7, 0.6][:k]
        return scores, self.chunks[:k]


class TestCrossEncoderReranker(unittest.TestCase):
    def test_reorders_candidates_and_preserves_embedding_score(self):
        candidates = [
            RetrievedChunk(0.9, make_chunk(0, "a.md", "alpha")),
            RetrievedChunk(0.8, make_chunk(1, "b.md", "beta")),
            RetrievedChunk(0.7, make_chunk(2, "c.md", "gamma")),
        ]
        model = FakeCrossEncoder([0.1, 0.95, 0.4])
        reranker = CrossEncoderReranker(model=model, batch_size=8)

        result = reranker.rerank("query", candidates, k=2)

        self.assertEqual([item.chunk.source for item in result], ["b.md", "c.md"])
        self.assertEqual([item.score for item in result], [0.95, 0.4])
        self.assertEqual([item.retrieval_score for item in result], [0.8, 0.7])
        self.assertEqual(model.calls[0]["batch_size"], 8)
        self.assertFalse(model.calls[0]["show_progress_bar"])

    def test_ties_preserve_original_candidate_order(self):
        candidates = [
            RetrievedChunk(0.9, make_chunk(0, "a.md", "alpha")),
            RetrievedChunk(0.8, make_chunk(1, "b.md", "beta")),
        ]
        reranker = CrossEncoderReranker(
            model=FakeCrossEncoder([0.5, 0.5])
        )

        result = reranker.rerank("query", candidates, k=2)

        self.assertEqual([item.chunk.source for item in result], ["a.md", "b.md"])

    def test_empty_inputs_do_not_call_model(self):
        model = FakeCrossEncoder([])
        reranker = CrossEncoderReranker(model=model)

        self.assertEqual(reranker.rerank("", [], k=3), [])
        self.assertEqual(model.calls, [])


class TestRetrieverWithReranker(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            make_chunk(0, "a.md", "alpha"),
            make_chunk(1, "b.md", "beta"),
            make_chunk(2, "c.md", "gamma"),
            make_chunk(3, "d.md", "delta"),
        ]

    def test_baseline_requests_only_k(self):
        store = FakeStore(self.chunks)
        retriever = Retriever(FakeEmbedder(), store)

        result = retriever.retrieve("query", k=2)

        self.assertEqual(store.requested_k, 2)
        self.assertEqual([item.chunk.source for item in result], ["a.md", "b.md"])

    def test_reranker_expands_candidate_pool(self):
        store = FakeStore(self.chunks)
        reranker = CrossEncoderReranker(
            model=FakeCrossEncoder([0.1, 0.2, 0.95, 0.3])
        )
        retriever = Retriever(
            FakeEmbedder(),
            store,
            reranker=reranker,
            candidate_k=4,
        )

        result = retriever.retrieve("query", k=2)

        self.assertEqual(store.requested_k, 4)
        self.assertEqual([item.chunk.source for item in result], ["c.md", "d.md"])

    def test_non_positive_k_returns_empty(self):
        store = FakeStore(self.chunks)
        retriever = Retriever(FakeEmbedder(), store)

        self.assertEqual(retriever.retrieve("query", k=0), [])
        self.assertIsNone(store.requested_k)


class TestPipelineRerankerIntegration(unittest.TestCase):
    def test_pipeline_uses_injected_reranker_without_network(self):
        embedder = HashEmbedder(dim=64)
        store = VectorStore(dim=embedder.dim)
        reranker = CrossEncoderReranker(
            model=FakeCrossEncoder([0.1, 0.9, 0.4])
        )
        pipeline = RAGPipeline(
            embedder=embedder,
            store=store,
            generator=None,
            chunker=Chunker(chunk_size=80, chunk_overlap=10),
            reranker=reranker,
            candidate_k=3,
        )
        pipeline.ingest(
            [
                Document(source="a.md", text="alpha topic"),
                Document(source="b.md", text="beta topic"),
                Document(source="c.md", text="gamma topic"),
            ]
        )

        result = pipeline.ask("topic", k=2)

        self.assertEqual(len(result.retrieved), 2)
        self.assertTrue(
            all(item.retrieval_score is not None for item in result.retrieved)
        )


if __name__ == "__main__":
    unittest.main()
