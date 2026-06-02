"""End-to-end smoke run: ingest sample_docs, retrieve, evaluate.

No OpenAI API key required — generation is skipped; retrieval-quality
eval (recall@k, MRR) is what gets reported. With sentence-transformers
installed, this uses the real MiniLM embedder; otherwise it falls back
to HashEmbedder and the numbers will be low.

Outputs:
    index/                       persisted vector store
    reports/smoke_eval.md        recall@k + MRR + per-case results
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from rag.chunker import Chunker, Document
from rag.embedder import make_default_embedder
from rag.eval import EvalCase, eval_retrieval
from rag.retriever import Retriever
from rag.vector_store import VectorStore

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_docs")
INDEX_DIR = "index"
REPORT_PATH = "reports/smoke_eval.md"


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
    store.add(chunks, embedder.embed([c.text for c in chunks]))
    store.save(INDEX_DIR)

    with open(os.path.join(SAMPLE_DIR, "eval_cases.json"), "r", encoding="utf-8") as fh:
        cases = [EvalCase(**c) for c in json.load(fh)]

    result = eval_retrieval(Retriever(embedder, store), cases, k=3)
    rows = "\n".join(
        f"| {r['question']} | {r['recall']:.0f} | {r['reciprocal_rank']:.3f} | {r['top_source']} |"
        for r in result.per_case
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(
            f"# RAG Assistant — Smoke Run\n\n"
            f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
            f"- **Embedder**: `{type(embedder).__name__}` (dim {embedder.dim})\n"
            f"- **Docs**: {len(docs)}  **Chunks**: {len(chunks)}\n"
            f"- **k**: 3\n\n"
            f"## Headline\n\n- **recall@3**: {result.recall_at_k:.3f}\n"
            f"- **MRR**: {result.mrr:.3f}\n\n"
            f"## Per-case results\n\n"
            f"| Question | Recall | RR | Top source |\n|---|---|---|---|\n{rows}\n"
        )
    print(f"Wrote {REPORT_PATH}: recall@3={result.recall_at_k:.3f}, MRR={result.mrr:.3f}")


if __name__ == "__main__":
    main()
