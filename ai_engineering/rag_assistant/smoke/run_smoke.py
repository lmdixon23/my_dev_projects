"""Run the versioned retrieval benchmark and write a Markdown report.

The default is the deterministic, network-free HashEmbedder baseline. Set
``RAG_EVAL_EMBEDDER=minilm`` for a local all-MiniLM-L6-v2 run.

Outputs:
    index/                 persisted vector store
    reports/smoke_eval.md  aggregate, category, and per-case results
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from rag.chunker import Chunker, Document
from rag.embedder import HashEmbedder, SentenceTransformerEmbedder
from rag.eval import (
    REQUIRED_BENCHMARK_TAGS,
    eval_retrieval,
    load_eval_cases,
    validate_eval_cases,
)
from rag.retriever import Retriever
from rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "sample_docs"
BASELINE_PATH = SAMPLE_DIR / "hash_baseline_v1.json"
INDEX_DIR = Path(os.environ.get("RAG_EVAL_INDEX", "index"))
REPORT_PATH = Path(os.environ.get("RAG_EVAL_REPORT", "reports/smoke_eval.md"))
EMBEDDER_MODE = os.environ.get("RAG_EVAL_EMBEDDER", "hash").lower()
MINILM_MODEL = os.environ.get(
    "RAG_EVAL_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


def _load_docs() -> list[Document]:
    return [
        Document(source=path.name, text=path.read_text(encoding="utf-8"))
        for path in sorted(SAMPLE_DIR.glob("*.md"))
    ]


def _load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _make_embedder(baseline: dict):
    if EMBEDDER_MODE == "hash":
        return HashEmbedder(dim=baseline["embedder"]["dim"]), "deterministic"
    if EMBEDDER_MODE == "minilm":
        return SentenceTransformerEmbedder(MINILM_MODEL), "local model"
    raise ValueError("RAG_EVAL_EMBEDDER must be 'hash' or 'minilm'")


def _format_rank(value) -> str:
    return str(value) if value is not None else "miss"


def main() -> None:
    baseline = _load_baseline()
    documents = _load_docs()
    cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
    validate_eval_cases(cases, [document.source for document in documents])

    embedder, mode_label = _make_embedder(baseline)
    chunker = Chunker(**baseline["chunker"])
    chunks = chunker.chunk_corpus(documents)
    store = VectorStore(dim=embedder.dim)
    store.add(chunks, embedder.embed([chunk.text for chunk in chunks]))
    store.save(str(INDEX_DIR))

    result = eval_retrieval(Retriever(embedder, store), cases, k=3)

    category_rows = "\n".join(
        (
            f"| `{tag}` | {result.by_tag[tag]['n_cases']} | "
            f"{result.by_tag[tag]['recall_at_1']:.3f} | "
            f"{result.by_tag[tag]['recall_at_3']:.3f} | "
            f"{result.by_tag[tag]['mrr']:.3f} |"
        )
        for tag in REQUIRED_BENCHMARK_TAGS
    )
    case_rows = "\n".join(
        (
            f"| `{row['id']}` | {', '.join(row['tags'])} | "
            f"{_format_rank(row['first_relevant_rank'])} | "
            f"{row['reciprocal_rank']:.3f} | {row['top_source']} |"
        )
        for row in result.per_case
    )

    baseline_note = ""
    if EMBEDDER_MODE == "hash":
        thresholds = baseline["regression_thresholds"]
        baseline_note = (
            "## Regression gate\n\n"
            f"- Minimum recall@1: {thresholds['min_recall_at_1']:.3f}\n"
            f"- Minimum recall@3: {thresholds['min_recall_at_3']:.3f}\n"
            f"- Minimum MRR: {thresholds['min_mrr']:.3f}\n"
            "- Each required category may lose at most one of its eight "
            "top-3 hits relative to the checked-in baseline.\n\n"
            f"{baseline['comparison_rule']}\n\n"
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# RAG Assistant - Retrieval Benchmark\n\n"
        f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
        f"- **Benchmark**: `{baseline['benchmark_version']}`\n"
        f"- **Embedder**: `{type(embedder).__name__}` ({mode_label}, dim {embedder.dim})\n"
        f"- **Documents**: {len(documents)}\n"
        f"- **Chunks**: {len(chunks)}\n"
        f"- **Cases**: {len(cases)}\n"
        f"- **Chunking**: {chunker.chunk_size} characters, {chunker.chunk_overlap} overlap\n\n"
        "## Metric definitions\n\n"
        "- **recall@1**: fraction of cases with an accepted source at rank 1.\n"
        "- **recall@3**: fraction with an accepted source in the top three.\n"
        "- **MRR**: mean reciprocal rank of the first accepted source; misses score zero.\n\n"
        "## Headline\n\n"
        f"- **recall@1**: {result.recall_at_1:.3f}\n"
        f"- **recall@3**: {result.recall_at_3:.3f}\n"
        f"- **MRR**: {result.mrr:.3f}\n\n"
        "## Required category slices\n\n"
        "| Category | Cases | recall@1 | recall@3 | MRR |\n"
        "|---|---:|---:|---:|---:|\n"
        f"{category_rows}\n\n"
        f"{baseline_note}"
        "## Per-case results\n\n"
        "| ID | Tags | First relevant rank | RR | Top source |\n"
        "|---|---|---:|---:|---|\n"
        f"{case_rows}\n\n"
        "## Claim boundary\n\n"
        "This is a versioned project baseline for regression testing. The corpus is "
        "small and synthetic, so the scores are not a leaderboard result or a claim "
        "about production retrieval quality.\n",
        encoding="utf-8",
    )

    print(
        f"Wrote {REPORT_PATH}: cases={result.n_cases}, "
        f"recall@1={result.recall_at_1:.3f}, "
        f"recall@3={result.recall_at_3:.3f}, MRR={result.mrr:.3f}"
    )


if __name__ == "__main__":
    main()
