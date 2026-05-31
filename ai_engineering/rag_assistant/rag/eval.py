"""Retrieval-quality evaluation.

The metric set is the small-but-honest one most RAG systems publish:

  * **recall@k**: did the retriever surface at least one expected chunk
    among the top-k results?
  * **MRR (mean reciprocal rank)**: how high up was the first relevant
    chunk on average? 1.0 == always first; 0.0 == never retrieved.

`EvalCase.relevant_sources` is the *set* of acceptable source IDs (any
substring match against `Chunk.source` counts), so it tolerates the
ground-truth file being chunked into multiple pieces.

For generation-quality eval, see the separate `llm_eval_harness` project
in this repo — keeping retrieval and generation eval in separate places
is the standard pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .retriever import RetrievedChunk, Retriever


@dataclass(frozen=True)
class EvalCase:
    question: str
    relevant_sources: List[str]


@dataclass
class EvalResult:
    n_cases: int
    recall_at_k: float
    mrr: float
    per_case: List[dict]

    def __str__(self) -> str:
        return (
            f"n={self.n_cases}  "
            f"recall@k={self.recall_at_k:.3f}  "
            f"MRR={self.mrr:.3f}"
        )


def _hits(retrieved: Sequence[RetrievedChunk], relevant: Sequence[str]) -> List[int]:
    """Return 1-based ranks of retrieved chunks whose source contains any
    of the relevant source markers."""
    out = []
    for rank, r in enumerate(retrieved, start=1):
        if any(marker in r.chunk.source for marker in relevant):
            out.append(rank)
    return out


def eval_retrieval(retriever: Retriever, cases: Sequence[EvalCase], k: int = 5) -> EvalResult:
    if not cases:
        return EvalResult(n_cases=0, recall_at_k=0.0, mrr=0.0, per_case=[])

    rec_sum = 0.0
    rr_sum = 0.0
    per_case = []
    for case in cases:
        retrieved = retriever.retrieve(case.question, k=k)
        hits = _hits(retrieved, case.relevant_sources)
        recall = 1.0 if hits else 0.0
        rr = 1.0 / hits[0] if hits else 0.0
        rec_sum += recall
        rr_sum += rr
        per_case.append({
            "question": case.question,
            "recall": recall,
            "reciprocal_rank": rr,
            "top_source": retrieved[0].chunk.source if retrieved else None,
        })

    return EvalResult(
        n_cases=len(cases),
        recall_at_k=rec_sum / len(cases),
        mrr=rr_sum / len(cases),
        per_case=per_case,
    )
