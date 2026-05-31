"""Embedding interface + two concrete implementations.

`Embedder` is the protocol every store talks to. Two implementations:

  * `SentenceTransformerEmbedder` — the production default; wraps
    `sentence-transformers/all-MiniLM-L6-v2` (384-d, fast on CPU).
  * `HashEmbedder` — deterministic, dependency-free, used by the test
    suite so CI doesn't have to download model weights. Quality is poor;
    do not use for real retrieval.

Vectors are L2-normalized so cosine similarity reduces to a dot product
in the FAISS index.
"""

from __future__ import annotations

import hashlib
from typing import List, Protocol, Sequence

import numpy as np


class Embedder(Protocol):
    """Anything that turns text into a (d,)-shaped float32 vector."""
    dim: int
    def embed(self, texts: Sequence[str]) -> np.ndarray: ...


def _normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (x / norms).astype(np.float32)


class HashEmbedder:
    """Deterministic dependency-free embedder for tests.

    Tokenizes on whitespace, hashes each token into `dim` buckets, sets
    that index to 1 (bag-of-hashed-tokens), then L2-normalizes. Bad
    embedding model — but stable across runs and machines, which is
    what tests need.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def _vectorize(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for tok in text.lower().split():
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[h] += 1.0
        return vec

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return _normalize(np.stack([self._vectorize(t) for t in texts]))


class SentenceTransformerEmbedder:
    """Wrap `sentence-transformers/all-MiniLM-L6-v2` (default) or any
    other model the caller specifies."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # Lazy import: keeps the test suite free of the (large) torch dep.
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        out = self._model.encode(list(texts), convert_to_numpy=True, show_progress_bar=False)
        return _normalize(out.astype(np.float32))


def make_default_embedder(model_name: str | None = None) -> Embedder:
    """Factory: return a SentenceTransformerEmbedder if installed, else
    fall back to HashEmbedder with a loud warning. The fallback exists
    so the CLI still runs in environments without torch (e.g. CI)."""
    try:
        return SentenceTransformerEmbedder(model_name) if model_name \
            else SentenceTransformerEmbedder()
    except ImportError:
        import warnings
        warnings.warn(
            "sentence-transformers not installed; falling back to HashEmbedder. "
            "Retrieval quality will be poor. `pip install sentence-transformers` "
            "to enable real embeddings."
        )
        return HashEmbedder()
