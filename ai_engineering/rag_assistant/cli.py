"""RAG Assistant CLI.

Subcommands:
    ingest   Index a directory of .md / .txt / .pdf files into a store on disk.
    ask      Query a saved store and print the model's answer.
    serve    Run the Flask API.
    eval     Run a retrieval-quality eval from a YAML/JSON cases file.

Usage:
    python cli.py ingest --docs-dir ./sample_docs --store ./index
    python cli.py ask --store ./index --question "What is RAG?"
    python cli.py ask --store ./index --question "What is RAG?" --rerank
    python cli.py serve --store ./index --port 8080
    python cli.py eval --store ./index --cases ./sample_docs/eval_cases.json -k 3
    python cli.py eval --store ./index --cases ./sample_docs/eval_cases.json -k 3 --rerank
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from rag import (
    Chunker,
    CrossEncoderReranker,
    DEFAULT_RERANKER_MODEL,
    Document,
    EvalCase,
    RAGPipeline,
    Reranker,
    eval_retrieval,
)
from rag.embedder import make_default_embedder
from rag.vector_store import VectorStore


SUPPORTED_EXTS = {".md", ".txt", ".pdf"}


def load_docs_from_dir(dir_path: str) -> List[Document]:
    docs: List[Document] = []
    for path in sorted(Path(dir_path).rglob("*")):
        if path.suffix.lower() not in SUPPORTED_EXTS:
            continue
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                print(f"skipping {path}: pypdf not installed", file=sys.stderr)
                continue
            text = "\n\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
        docs.append(Document(source=str(path), text=text))
    return docs


def _build_reranker(args: argparse.Namespace) -> Optional[Reranker]:
    if not getattr(args, "rerank", False):
        return None
    return CrossEncoderReranker(model_name=args.reranker_model)


def _add_reranker_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="re-rank a larger candidate pool with a cross-encoder",
    )
    parser.add_argument(
        "--reranker-model",
        default=DEFAULT_RERANKER_MODEL,
        help="sentence-transformers CrossEncoder model name",
    )
    parser.add_argument(
        "--candidate-k",
        type=int,
        default=20,
        help="embedding candidates passed to the re-ranker",
    )


def cmd_ingest(args: argparse.Namespace) -> None:
    docs = load_docs_from_dir(args.docs_dir)
    if not docs:
        sys.exit(f"no .md/.txt/.pdf files found under {args.docs_dir}")
    pipeline = RAGPipeline.from_env()
    pipeline.chunker = Chunker(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    n = pipeline.ingest(docs)
    pipeline.save(args.store)
    print(f"Indexed {len(docs)} docs -> {n} chunks; saved to {args.store}")


def cmd_ask(args: argparse.Namespace) -> None:
    pipeline = RAGPipeline.load(
        args.store,
        reranker=_build_reranker(args),
        candidate_k=args.candidate_k,
    )
    result = pipeline.ask(args.question, k=args.k)
    print(f"\nAnswer:\n{result.answer}\n")
    if result.sources:
        print(f"Sources: {', '.join(result.sources)}")
    print(f"Retrieved {len(result.retrieved)} chunks, used {result.tokens_used} tokens.")


def cmd_serve(args: argparse.Namespace) -> None:
    from app import build_app  # local import to avoid forcing Flask for non-serve users
    build_app(args.store).run(host="0.0.0.0", port=args.port)


def cmd_eval(args: argparse.Namespace) -> None:
    with open(args.cases, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    cases = [EvalCase(question=c["question"], relevant_sources=c["relevant_sources"]) for c in raw]
    embedder = make_default_embedder()
    store = VectorStore.load(args.store)
    if embedder.dim != store.dim:
        sys.exit(f"embedder dim {embedder.dim} != store dim {store.dim}; reindex.")
    from rag.retriever import Retriever
    result = eval_retrieval(
        Retriever(
            embedder,
            store,
            reranker=_build_reranker(args),
            candidate_k=args.candidate_k,
        ),
        cases,
        k=args.k,
    )
    print(result)
    for row in result.per_case:
        print(f"  - {row['question'][:60]:60s}  recall={row['recall']:.0f}  rr={row['reciprocal_rank']:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("--docs-dir", required=True)
    p_ingest.add_argument("--store", required=True)
    p_ingest.add_argument("--chunk-size", type=int, default=800)
    p_ingest.add_argument("--chunk-overlap", type=int, default=100)
    p_ingest.set_defaults(func=cmd_ingest)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("--store", required=True)
    p_ask.add_argument("--question", required=True)
    p_ask.add_argument("-k", type=int, default=5)
    _add_reranker_args(p_ask)
    p_ask.set_defaults(func=cmd_ask)

    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--store", required=True)
    p_serve.add_argument("--port", type=int, default=8080)
    p_serve.set_defaults(func=cmd_serve)

    p_eval = sub.add_parser("eval")
    p_eval.add_argument("--store", required=True)
    p_eval.add_argument("--cases", required=True)
    p_eval.add_argument("-k", type=int, default=5)
    _add_reranker_args(p_eval)
    p_eval.set_defaults(func=cmd_eval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
