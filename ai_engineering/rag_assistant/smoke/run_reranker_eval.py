"""Compare embedding-only retrieval against optional cross-encoder re-ranking.

This script requires sentence-transformers model weights. It does not require
an OpenAI API key. The checked-in five-case suite is saturated, so the report
is a provisional measurement until the expanded benchmark in issue #18 lands.

Outputs:
    reports/reranker_eval.md
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from rag.chunker import Chunker, Document
from rag.embedder import make_default_embedder
from rag.eval import EvalCase, eval_retrieval
from rag.reranker import CrossEncoderReranker, DEFAULT_RERANKER_MODEL
from rag.retriever import Retriever
from rag.vector_store import VectorStore


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_docs")
REPORT_PATH = "reports/reranker_eval.md"
K = int(os.environ.get("RERANKER_EVAL_K", "3"))
CANDIDATE_K = int(os.environ.get("RERANKER_CANDIDATES", "20"))
MODEL_NAME = os.environ.get("RERANKER_MODEL", DEFAULT_RERANKER_MODEL)


def _load_docs() -> list[Document]:
    docs = []
    for name in sorted(os.listdir(SAMPLE_DIR)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(SAMPLE_DIR, name), "r", encoding="utf-8") as fh:
            docs.append(Document(source=name, text=fh.read()))
    return docs


def main() -> None:
    os.makedirs("reports", exist_ok=True)
    docs = _load_docs()
    embedder = make_default_embedder()

    chunker = Chunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_corpus(docs)
    store = VectorStore(dim=embedder.dim)
    store.add(chunks, embedder.embed([chunk.text for chunk in chunks]))

    with open(
        os.path.join(SAMPLE_DIR, "eval_cases.json"),
        "r",
        encoding="utf-8",
    ) as fh:
        cases = [EvalCase(**case) for case in json.load(fh)]

    baseline = eval_retrieval(
        Retriever(embedder, store),
        cases,
        k=K,
    )
    reranked = eval_retrieval(
        Retriever(
            embedder,
            store,
            reranker=CrossEncoderReranker(model_name=MODEL_NAME),
            candidate_k=CANDIDATE_K,
        ),
        cases,
        k=K,
    )

    recall_delta = reranked.recall_at_k - baseline.recall_at_k
    mrr_delta = reranked.mrr - baseline.mrr
    rows = "\n".join(
        (
            f"| {base['question']} | {base['reciprocal_rank']:.3f} | "
            f"{rerank['reciprocal_rank']:.3f} | "
            f"{rerank['reciprocal_rank'] - base['reciprocal_rank']:+.3f} |"
        )
        for base, rerank in zip(baseline.per_case, reranked.per_case)
    )

    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(
            "# RAG Assistant - Re-ranker Evaluation\n\n"
            f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
            f"- **Embedder**: `{type(embedder).__name__}`\n"
            f"- **Re-ranker**: `{MODEL_NAME}`\n"
            f"- **Cases**: {len(cases)}\n"
            f"- **k**: {K}\n"
            f"- **Candidate pool**: {CANDIDATE_K}\n\n"
            "## Aggregate comparison\n\n"
            "| Configuration | recall@k | MRR |\n"
            "|---|---:|---:|\n"
            f"| Embedding only | {baseline.recall_at_k:.3f} | {baseline.mrr:.3f} |\n"
            f"| Cross-encoder re-ranked | {reranked.recall_at_k:.3f} | {reranked.mrr:.3f} |\n"
            f"| Delta | {recall_delta:+.3f} | {mrr_delta:+.3f} |\n\n"
            "## Per-case reciprocal-rank comparison\n\n"
            "| Question | Baseline RR | Re-ranked RR | Delta |\n"
            "|---|---:|---:|---:|\n"
            f"{rows}\n\n"
            "## Interpretation boundary\n\n"
            "This is a five-case smoke evaluation over three small documents. "
            "It records the observed delta but is not large enough to establish "
            "a reliable quality lift. Re-run against the expanded benchmark from "
            "issue #18 before making a comparative performance claim.\n"
        )

    print(
        f"Wrote {REPORT_PATH}: "
        f"recall delta={recall_delta:+.3f}, MRR delta={mrr_delta:+.3f}"
    )


if __name__ == "__main__":
    main()
