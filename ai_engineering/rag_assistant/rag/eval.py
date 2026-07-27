"""Deterministic retrieval-quality evaluation.

The evaluator reports three complementary ranking metrics:

* ``recall@1``: fraction of cases with a relevant source at rank 1.
* ``recall@3``: fraction of cases with a relevant source in the top 3.
* ``MRR``: mean reciprocal rank of the first relevant source.

``EvalCase.relevant_sources`` remains a set of acceptable source markers. A
marker matches when it is contained in ``RetrievedChunk.chunk.source``, so a
single labeled source can still be split into multiple chunks. Stable case IDs
and tags are optional for backward compatibility, but the checked-in benchmark
validates and requires them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from .retriever import RetrievedChunk, Retriever


REQUIRED_BENCHMARK_TAGS = (
    "direct_lookup",
    "paraphrase",
    "terminology",
    "cross_chunk",
    "hard_negative",
)


@dataclass(frozen=True)
class EvalCase:
    question: str
    relevant_sources: List[str]
    id: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    n_cases: int
    k: int
    recall_at_1: float
    recall_at_3: float
    recall_at_k: float
    mrr: float
    per_case: List[dict]
    by_tag: Dict[str, dict]

    def __str__(self) -> str:
        parts = [
            f"n={self.n_cases}",
            f"recall@1={self.recall_at_1:.3f}",
            f"recall@3={self.recall_at_3:.3f}",
        ]
        if self.k not in (1, 3):
            parts.append(f"recall@{self.k}={self.recall_at_k:.3f}")
        parts.append(f"MRR={self.mrr:.3f}")
        return "  ".join(parts)


def load_eval_cases(path: str | Path) -> List[EvalCase]:
    """Load JSON cases while preserving the legacy two-field schema."""
    with open(path, "r", encoding="utf-8") as handle:
        raw_cases = json.load(handle)

    if not isinstance(raw_cases, list):
        raise ValueError("evaluation cases must be a JSON list")

    cases: List[EvalCase] = []
    for index, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError("each evaluation case must be an object")

        question = raw.get("question", "")
        case_id = raw.get("id", "")
        sources = raw.get("relevant_sources", [])
        tags = raw.get("tags", [])
        if not isinstance(question, str) or not isinstance(case_id, str):
            raise ValueError(f"case #{index} has non-string id or question")
        if not isinstance(sources, list) or any(
            not isinstance(source, str) for source in sources
        ):
            raise ValueError(f"case #{index} relevant_sources must be a string list")
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise ValueError(f"case #{index} tags must be a string list")

        cases.append(
            EvalCase(
                question=question,
                relevant_sources=list(sources),
                id=case_id,
                tags=list(tags),
            )
        )
    return cases


def validate_eval_cases(
    cases: Sequence[EvalCase],
    available_sources: Iterable[str] | None = None,
    required_tags: Sequence[str] = REQUIRED_BENCHMARK_TAGS,
) -> None:
    """Raise ``ValueError`` when a benchmark dataset is malformed."""
    source_set = set(available_sources) if available_sources is not None else None
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    represented_tags: set[str] = set()

    for index, case in enumerate(cases, start=1):
        label = case.id or f"case #{index}"
        if not case.id.strip():
            raise ValueError(f"{label} has an empty id")
        if case.id in seen_ids:
            raise ValueError(f"duplicate case id: {case.id}")
        seen_ids.add(case.id)

        question = case.question.strip()
        if not question:
            raise ValueError(f"{label} has an empty question")
        if question in seen_questions:
            raise ValueError(f"duplicate question: {question}")
        seen_questions.add(question)

        sources = [source.strip() for source in case.relevant_sources]
        if not sources or any(not source for source in sources):
            raise ValueError(f"{label} has empty relevant-source labels")
        if len(sources) != len(set(sources)):
            raise ValueError(f"{label} has duplicate relevant-source labels")
        if source_set is not None:
            missing = sorted(set(sources) - source_set)
            if missing:
                raise ValueError(
                    f"{label} references missing sources: {', '.join(missing)}"
                )

        tags = [tag.strip() for tag in case.tags]
        if not tags or any(not tag for tag in tags):
            raise ValueError(f"{label} has empty tags")
        if len(tags) != len(set(tags)):
            raise ValueError(f"{label} has duplicate tags")
        represented_tags.update(tags)

    missing_tags = sorted(set(required_tags) - represented_tags)
    if missing_tags:
        raise ValueError(
            "benchmark is missing required tags: " + ", ".join(missing_tags)
        )


def _hits(
    retrieved: Sequence[RetrievedChunk], relevant: Sequence[str]
) -> List[int]:
    """Return 1-based ranks whose source contains an accepted marker."""
    return [
        rank
        for rank, result in enumerate(retrieved, start=1)
        if any(marker in result.chunk.source for marker in relevant)
    ]


def _aggregate(rows: Sequence[dict], k: int) -> dict:
    if not rows:
        return {
            "n_cases": 0,
            "recall_at_1": 0.0,
            "recall_at_3": 0.0,
            "recall_at_k": 0.0,
            "mrr": 0.0,
        }

    count = len(rows)
    return {
        "n_cases": count,
        "recall_at_1": sum(row["recall_at_1"] for row in rows) / count,
        "recall_at_3": sum(row["recall_at_3"] for row in rows) / count,
        "recall_at_k": sum(row["recall_at_k"] for row in rows) / count,
        "mrr": sum(row["reciprocal_rank"] for row in rows) / count,
    }


def eval_retrieval(
    retriever: Retriever,
    cases: Sequence[EvalCase],
    k: int = 5,
) -> EvalResult:
    if k < 1:
        raise ValueError("k must be >= 1")
    if not cases:
        return EvalResult(
            n_cases=0,
            k=k,
            recall_at_1=0.0,
            recall_at_3=0.0,
            recall_at_k=0.0,
            mrr=0.0,
            per_case=[],
            by_tag={},
        )

    retrieval_depth = max(3, k)
    per_case: List[dict] = []

    for case in cases:
        retrieved = retriever.retrieve(case.question, k=retrieval_depth)
        hits = _hits(retrieved, case.relevant_sources)
        first_rank = hits[0] if hits else None
        recall_at_1 = 1.0 if first_rank is not None and first_rank <= 1 else 0.0
        recall_at_3 = 1.0 if first_rank is not None and first_rank <= 3 else 0.0
        recall_at_k = 1.0 if first_rank is not None and first_rank <= k else 0.0
        reciprocal_rank = 1.0 / first_rank if first_rank is not None else 0.0

        per_case.append(
            {
                "id": case.id,
                "question": case.question,
                "tags": list(case.tags),
                "relevant_sources": list(case.relevant_sources),
                "hit_ranks": hits,
                "first_relevant_rank": first_rank,
                "recall_at_1": recall_at_1,
                "recall_at_3": recall_at_3,
                "recall_at_k": recall_at_k,
                "recall": recall_at_k,
                "reciprocal_rank": reciprocal_rank,
                "top_source": retrieved[0].chunk.source if retrieved else None,
            }
        )

    aggregate = _aggregate(per_case, k)
    rows_by_tag: Dict[str, List[dict]] = {}
    for row in per_case:
        for tag in row["tags"]:
            rows_by_tag.setdefault(tag, []).append(row)
    by_tag = {
        tag: _aggregate(rows, k)
        for tag, rows in sorted(rows_by_tag.items())
    }

    return EvalResult(
        n_cases=len(cases),
        k=k,
        recall_at_1=aggregate["recall_at_1"],
        recall_at_3=aggregate["recall_at_3"],
        recall_at_k=aggregate["recall_at_k"],
        mrr=aggregate["mrr"],
        per_case=per_case,
        by_tag=by_tag,
    )
