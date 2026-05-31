"""End-to-end ingest + retrieve + generate pipeline.

`RAGPipeline.ingest(docs)` runs the chunker + embedder + store.
`RAGPipeline.ask(question, k=5)` runs the retriever + generator.

`from_env()` reads `OPENAI_API_KEY`, `OPENAI_MODEL`, `EMBEDDING_MODEL`,
so the CLI and serving layers share configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Sequence

from dotenv import load_dotenv

from .chunker import Chunk, Chunker, Document
from .embedder import Embedder, make_default_embedder
from .generator import GenerationResult, Generator
from .retriever import RetrievedChunk, Retriever
from .vector_store import VectorStore


@dataclass
class AskResult:
    answer: str
    sources: List[str]
    retrieved: List[RetrievedChunk]
    tokens_used: int


class RAGPipeline:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        generator: Optional[Generator] = None,
        chunker: Optional[Chunker] = None,
    ):
        self.embedder = embedder
        self.store = store
        self.retriever = Retriever(embedder, store)
        self.generator = generator
        self.chunker = chunker or Chunker()

    # ---- Construction helpers ------------------------------------------ #
    @classmethod
    def from_env(
        cls,
        embedder: Optional[Embedder] = None,
        store: Optional[VectorStore] = None,
    ) -> "RAGPipeline":
        load_dotenv()
        emb = embedder or make_default_embedder(os.getenv("EMBEDDING_MODEL"))
        st = store or VectorStore(dim=emb.dim)
        gen = Generator()
        return cls(embedder=emb, store=st, generator=gen)

    # ---- Ingest -------------------------------------------------------- #
    def ingest(self, docs: Sequence[Document]) -> int:
        """Chunk + embed + add to the vector store. Returns chunk count."""
        chunks: List[Chunk] = self.chunker.chunk_corpus(docs)
        if not chunks:
            return 0
        embeddings = self.embedder.embed([c.text for c in chunks])
        self.store.add(chunks, embeddings)
        return len(chunks)

    # ---- Ask ----------------------------------------------------------- #
    def ask(self, question: str, k: int = 5) -> AskResult:
        retrieved = self.retriever.retrieve(question, k=k)
        if self.generator is None:
            return AskResult(
                answer="(no generator configured)",
                sources=sorted({r.chunk.source for r in retrieved}),
                retrieved=retrieved,
                tokens_used=0,
            )
        gen: GenerationResult = self.generator.generate(question, retrieved)
        return AskResult(
            answer=gen.answer,
            sources=gen.sources,
            retrieved=retrieved,
            tokens_used=gen.tokens_used,
        )

    # ---- Persistence --------------------------------------------------- #
    def save(self, dir_path: str) -> None:
        self.store.save(dir_path)

    @classmethod
    def load(
        cls,
        dir_path: str,
        embedder: Optional[Embedder] = None,
        generator: Optional[Generator] = None,
    ) -> "RAGPipeline":
        store = VectorStore.load(dir_path)
        emb = embedder or make_default_embedder()
        if emb.dim != store.dim:
            raise RuntimeError(
                f"embedder dim {emb.dim} does not match stored index dim {store.dim}; "
                "did you change EMBEDDING_MODEL since indexing?"
            )
        return cls(embedder=emb, store=store, generator=generator or Generator())
