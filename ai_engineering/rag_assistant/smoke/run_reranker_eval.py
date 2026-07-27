"""Compare MiniLM embedding retrieval with optional cross-encoder re-ranking.

This command uses the versioned 40-case benchmark. It requires local model
weights but no OpenAI API key.

Outputs:
    reports/reranker_eval.md
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from rag.chunker import Chunker, Document
from rag.embedder import SentenceTransformerEmbedder
from rag.eval import (
    REQUIRED_BENCHMARK_TAGS,
    eval_retrieval,
    load_eval_cases,
    validate_eval_cases,
)
from rag.reranker import CrossEncoderReranker, DEFAULT_RERANKER_MODEL
from rag.retriever import Retriever
from rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "sample_docs"
BASELINE_PATH = SAMPLE_DIR / "hash_baseline_v1.json"
REPORT_PATH = Path(os.environ.get("RERANKER_EVAL_REPORT", "reports/reranker_eval.md"))
CANDIDATE_K = int(os.environ.get("RERANKER_CANDIDATES", "20"))
EMBEDDING_MODEL = os.environ.get(
    "RAG_EVAL_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
RERANKER_MODEL = os.environ.get("RERANKER_MODEL", DEFAULT_RERANKER_MODEL)


def _load_docs() -> list[Document]:
    return [
        Document(source=path.name, text=path.read_text(encoding="utf-8"))
        for path in sorted(SAMPLE_DIR.glob("*.md"))
    ]


def _rank(row: dict) -> str:
    value = row["first_relevant_rank"]
    return str(value) if value is not None else "miss"


def main() -> None:
    baseline_spec = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    documents = _load_docs()
    cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
    validate_eval_cases(cases, [document.source for document in documents])

    embedder = SentenceTransformerEmbedder(EMBEDDING_MODEL)
    chunker = Chunker(**baseline_spec["chunker"])
    chunks = chunker.chunk_corpus(documents)
    store = VectorStore(dim=embedder.dim)
    store.add(chunks, embedder.embed([chunk.text for chunk in chunks]))

    embedding_only = eval_retrieval(
        Retriever(embedder, store),
        cases,
        k=3,
    )
    reranked = eval_retrieval(
        Retriever(
            embedder,
            store,
            reranker=CrossEncoderReranker(model_name=RERANKER_MODEL),
            candidate_k=CANDIDATE_K,
        ),
        cases,
        k=3,
    )

    aggregate_rows = (
        f"| Embedding only | {embedding_only.recall_at_1:.3f} | "
        f"{embedding_only.recall_at_3:.3f} | {embedding_only.mrr:.3f} |\n"
        f"| Cross-encoder re-ranked | {reranked.recall_at_1:.3f} | "
        f"{reranked.recall_at_3:.3f} | {reranked.mrr:.3f} |\n"
        f"| Delta | {reranked.recall_at_1 - embedding_only.recall_at_1:+.3f} | "
        f"{reranked.recall_at_3 - embedding_only.recall_at_3:+.3f} | "
        f"{reranked.mrr - embedding_only.mrr:+.3f} |"
    )
    category_rows = "\n".join(
        (
            f"| `{tag}` | {embedding_only.by_tag[tag]['recall_at_3']:.3f} | "
            f"{reranked.by_tag[tag]['recall_at_3']:.3f} | "
            f"{reranked.by_tag[tag]['recall_at_3'] - embedding_only.by_tag[tag]['recall_at_3']:+.3f} | "
            f"{embedding_only.by_tag[tag]['mrr']:.3f} | "
            f"{reranked.by_tag[tag]['mrr']:.3f} |"
        )
        for tag in REQUIRED_BENCHMARK_TAGS
    )
    case_rows = "\n".join(
        (
            f"| `{base['id']}` | {', '.join(base['tags'])} | {_rank(base)} | "
            f"{_rank(rerank)} | {base['reciprocal_rank']:.3f} | "
            f"{rerank['reciprocal_rank']:.3f} | "
            f"{rerank['reciprocal_rank'] - base['reciprocal_rank']:+.3f} |"
        )
        for base, rerank in zip(embedding_only.per_case, reranked.per_case)
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# RAG Assistant - Re-ranker Evaluation\n\n"
        f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
        f"- **Benchmark**: `{baseline_spec['benchmark_version']}`\n"
        f"- **Embedding model**: `{EMBEDDING_MODEL}`\n"
        f"- **Re-ranker**: `{RERANKER_MODEL}`\n"
        f"- **Documents**: {len(documents)}\n"
        f"- **Chunks**: {len(chunks)}\n"
        f"- **Cases**: {len(cases)}\n"
        f"- **Candidate pool**: {CANDIDATE_K}\n\n"
        "## Aggregate comparison\n\n"
        "| Configuration | recall@1 | recall@3 | MRR |\n"
        "|---|---:|---:|---:|\n"
        f"{aggregate_rows}\n\n"
        "## Required category slices\n\n"
        "| Category | Base recall@3 | Re-ranked recall@3 | Delta | Base MRR | Re-ranked MRR |\n"
        "|---|---:|---:|---:|---:|---:|\n"
        f"{category_rows}\n\n"
        "## Per-case comparison\n\n"
        "| ID | Tags | Base rank | Re-ranked rank | Base RR | Re-ranked RR | Delta |\n"
        "|---|---|---:|---:|---:|---:|---:|\n"
        f"{case_rows}\n\n"
        "## Interpretation boundary\n\n"
        "This comparison is reproducible on the checked-in project benchmark. "
        "It is more discriminative than the earlier five-case smoke suite, but it "
        "remains a small synthetic corpus and is not a leaderboard or production "
        "quality claim.\n",
        encoding="utf-8",
    )

    print(
        f"Wrote {REPORT_PATH}: "
        f"recall@1 delta={reranked.recall_at_1 - embedding_only.recall_at_1:+.3f}, "
        f"recall@3 delta={reranked.recall_at_3 - embedding_only.recall_at_3:+.3f}, "
        f"MRR delta={reranked.mrr - embedding_only.mrr:+.3f}"
    )


if __name__ == "__main__":
    main()
