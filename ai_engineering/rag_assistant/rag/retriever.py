"""Thin wrapper that wires an Embedder and a VectorStore together.

Keeping retrieval as its own class (rather than a free function) means
swapping in a different backend (Chroma, Pinecone, Weaviate) only
requires writing a new `Retriever` subclass. An optional re-ranker can
re-score a larger candidate pool before the final top-k is returned.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .chunker import Chunk
from .embedder import Embedder
from .reranker import Reranker
from .vector_store import VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    score: float
    chunk: Chunk
    retrieval_score: Optional[float] = None


class Retriever:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        reranker: Optional[Reranker] = None,
        candidate_k: int = 20,
    ):
        if embedder.dim != store.dim:
            raise ValueError(
                f"embedder dim {embedder.dim} != store dim {store.dim}"
            )
        if candidate_k < 1:
            raise ValueError("candidate_k must be >= 1")
        self.embedder = embedder
        self.store = store
        self.reranker = reranker
        self.candidate_k = candidate_k

    def retrieve(self, query: str, k: int = 5) -> List[RetrievedChunk]:
        if not query.strip() or k <= 0:
            return []

        pool_k = max(k, self.candidate_k) if self.reranker is not None else k
        qvec = self.embedder.embed([query])
        scores, chunks = self.store.search(qvec, k=pool_k)
        candidates = [
            RetrievedChunk(score=float(score), chunk=chunk)
            for score, chunk in zip(scores, chunks)
        ]

        if self.reranker is None:
            return candidates[:k]
        return self.reranker.rerank(query, candidates, k)
