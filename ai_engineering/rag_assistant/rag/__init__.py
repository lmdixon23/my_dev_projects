"""RAG (Retrieval-Augmented Generation) toolkit.

Exposes chunking, embedding, storage, retrieval, optional re-ranking,
generation, the end-to-end pipeline, and versioned retrieval evaluation.
"""

from .chunker import Chunker, Document, Chunk
from .embedder import Embedder, HashEmbedder
from .vector_store import VectorStore
from .reranker import (
    CrossEncoderReranker,
    DEFAULT_RERANKER_MODEL,
    Reranker,
)
from .retriever import Retriever, RetrievedChunk
from .generator import Generator
from .pipeline import RAGPipeline
from .eval import (
    REQUIRED_BENCHMARK_TAGS,
    EvalCase,
    EvalResult,
    eval_retrieval,
    load_eval_cases,
    validate_eval_cases,
)

__all__ = [
    "Chunker", "Document", "Chunk",
    "Embedder", "HashEmbedder",
    "VectorStore",
    "Reranker", "CrossEncoderReranker", "DEFAULT_RERANKER_MODEL",
    "Retriever", "RetrievedChunk",
    "Generator",
    "RAGPipeline",
    "REQUIRED_BENCHMARK_TAGS",
    "eval_retrieval", "load_eval_cases", "validate_eval_cases",
    "EvalResult", "EvalCase",
]
