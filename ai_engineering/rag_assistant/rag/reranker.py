"""Optional cross-encoder re-ranking for retrieved chunks.

The production implementation wraps sentence-transformers CrossEncoder, while
the constructor accepts an injected model so tests can remain deterministic
and network-free.
"""

from __future__ import annotations

from typing import List, Optional, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .retriever import RetrievedChunk


DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderModel(Protocol):
    def predict(
        self,
        sentences,
        *,
        batch_size: int,
        show_progress_bar: bool,
    ): ...


class Reranker(Protocol):
    def rerank(
        self,
        query: str,
        candidates: Sequence["RetrievedChunk"],
        k: int,
    ) -> List["RetrievedChunk"]: ...


class CrossEncoderReranker:
    """Re-score query/chunk pairs with a sentence-transformers cross-encoder."""

    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        *,
        batch_size: int = 32,
        model: Optional[CrossEncoderModel] = None,
    ):
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self.model_name = model_name
        self.batch_size = batch_size
        if model is None:
            from sentence_transformers import CrossEncoder  # type: ignore

            model = CrossEncoder(model_name)
        self._model = model

    def rerank(
        self,
        query: str,
        candidates: Sequence["RetrievedChunk"],
        k: int,
    ) -> List["RetrievedChunk"]:
        if k <= 0 or not query.strip() or not candidates:
            return []

        pairs = [(query, candidate.chunk.text) for candidate in candidates]
        raw_scores = self._model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        scores = [float(score) for score in raw_scores]
        if len(scores) != len(candidates):
            raise RuntimeError(
                "cross-encoder returned "
                f"{len(scores)} scores for {len(candidates)} candidates"
            )

        from .retriever import RetrievedChunk

        ranked = sorted(
            enumerate(zip(candidates, scores)),
            key=lambda item: (-item[1][1], item[0]),
        )
        return [
            RetrievedChunk(
                score=rerank_score,
                chunk=candidate.chunk,
                retrieval_score=(
                    candidate.retrieval_score
                    if candidate.retrieval_score is not None
                    else candidate.score
                ),
            )
            for _, (candidate, rerank_score) in ranked[:k]
        ]
