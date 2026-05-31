"""Thin wrapper that wires an Embedder and a VectorStore together.

Keeping retrieval as its own class (rather than a free function) means
swapping in a different backend (Chroma, Pinecone, Weaviate) only
requires writing a new `Retriever` subclass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .chunker import Chunk
from .embedder import Embedder
from .vector_store import VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    score: float
    chunk: Chunk


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore):
        if embedder.dim != store.dim:
            raise ValueError(
                f"embedder dim {embedder.dim} != store dim {store.dim}"
            )
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: str, k: int = 5) -> List[RetrievedChunk]:
        if not query.strip():
            return []
        qvec = self.embedder.embed([query])
        scores, chunks = self.store.search(qvec, k=k)
        return [RetrievedChunk(score=float(s), chunk=c) for s, c in zip(scores, chunks)]
