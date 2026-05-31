"""FAISS-backed vector store with metadata.

FAISS doesn't carry metadata itself, so we keep a parallel list of
chunks aligned by index. The store also supports a pure-NumPy fallback
for environments without faiss (e.g. some Windows / CI setups).

Serialization writes the FAISS index + a JSON sidecar with the chunk
metadata, so reloading is a two-file operation, not a pickle.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import List, Optional

import numpy as np

from .chunker import Chunk


class VectorStore:
    """Inner-product nearest-neighbor over L2-normalized embeddings
    (== cosine similarity)."""

    def __init__(self, dim: int):
        self.dim = dim
        self._chunks: List[Chunk] = []
        self._embeddings: Optional[np.ndarray] = None  # (N, dim)
        self._faiss_index = None
        try:
            import faiss  # type: ignore
            self._faiss = faiss
            self._faiss_index = faiss.IndexFlatIP(dim)
        except ImportError:
            self._faiss = None  # NumPy fallback

    # ------------------------------------------------------------------ #
    def add(self, chunks: List[Chunk], embeddings: np.ndarray) -> None:
        if embeddings.ndim != 2 or embeddings.shape[1] != self.dim:
            raise ValueError(
                f"expected (N, {self.dim}) embeddings, got {embeddings.shape}"
            )
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("chunks and embeddings have different lengths")
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        self._chunks.extend(chunks)
        self._embeddings = (
            embeddings if self._embeddings is None
            else np.vstack([self._embeddings, embeddings])
        )
        if self._faiss is not None:
            self._faiss_index.add(embeddings)

    # ------------------------------------------------------------------ #
    def search(self, query: np.ndarray, k: int = 5):
        """Return (scores, chunks) of the top-k nearest chunks. Scores
        are cosine similarities in [-1, 1] (1 == perfect match)."""
        if len(self._chunks) == 0:
            return [], []
        k = min(k, len(self._chunks))
        if query.ndim == 1:
            query = query.reshape(1, -1)
        if query.dtype != np.float32:
            query = query.astype(np.float32)

        if self._faiss is not None:
            scores, idx = self._faiss_index.search(query, k)
            scores, idx = scores[0].tolist(), idx[0].tolist()
        else:
            sims = (self._embeddings @ query.T).reshape(-1)
            idx = np.argsort(-sims)[:k].tolist()
            scores = [float(sims[i]) for i in idx]

        return scores, [self._chunks[i] for i in idx]

    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        return len(self._chunks)

    # ------------------------------------------------------------------ #
    def save(self, dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)
        np.save(os.path.join(dir_path, "embeddings.npy"), self._embeddings)
        with open(os.path.join(dir_path, "chunks.json"), "w", encoding="utf-8") as fh:
            json.dump([asdict(c) for c in self._chunks], fh)

    @classmethod
    def load(cls, dir_path: str) -> "VectorStore":
        embeddings = np.load(os.path.join(dir_path, "embeddings.npy"))
        with open(os.path.join(dir_path, "chunks.json"), "r", encoding="utf-8") as fh:
            chunks = [Chunk(**c) for c in json.load(fh)]
        store = cls(dim=embeddings.shape[1])
        store.add(chunks, embeddings)
        return store
