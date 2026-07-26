"""RAG (Retrieval-Augmented Generation) toolkit.

Exposes:
    Chunker        - split documents into overlapping chunks
    Embedder       - convert chunks to dense vectors
    VectorStore    - FAISS-backed nearest-neighbor index with metadata
    Retriever      - embedding retrieval with optional cross-encoder re-ranking
    Reranker       - protocol for re-ordering an initial candidate pool
    Generator      - calls the OpenAI Chat Completions API with retrieved context
    RAGPipeline    - end-to-end: ingest -> retrieve -> generate
    eval_retrieval - retrieval-quality metrics (recall@k, MRR)

`RAGPipeline.from_env()` reads `OPENAI_API_KEY`, `OPENAI_MODEL`, and
`EMBEDDING_MODEL` so test fixtures and the CLI agree on configuration.
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
from .eval import eval_retrieval, EvalResult, EvalCase

__all__ = [
    "Chunker", "Document", "Chunk",
    "Embedder", "HashEmbedder",
    "VectorStore",
    "Reranker", "CrossEncoderReranker", "DEFAULT_RERANKER_MODEL",
    "Retriever", "RetrievedChunk",
    "Generator",
    "RAGPipeline",
    "eval_retrieval", "EvalResult", "EvalCase",
]
