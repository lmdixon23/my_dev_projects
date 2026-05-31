"""Document chunking with overlap.

Chunking strategy matters more for retrieval quality than most teams
realize. This module implements a simple but effective approach:

  1. Split on paragraph breaks (`\\n\\n+`) first.
  2. Greedily pack paragraphs into windows up to `chunk_size` chars.
  3. When a paragraph alone exceeds `chunk_size`, fall back to splitting
     it on sentence boundaries.
  4. Each chunk overlaps the previous one by `chunk_overlap` chars to
     avoid splitting an answer across two chunks the retriever might
     score differently.

This is intentionally not a token-based chunker because tokenization
depends on the LLM family; using characters makes the chunker
LLM-agnostic. Token budgeting still happens at generation time in
`Generator`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence

# Sentence splitter that's good enough for English without dragging in nltk.
_SENT_RE = re.compile(r"(?<=[.!?])\s+")
_PARA_RE = re.compile(r"\n{2,}")


@dataclass(frozen=True)
class Document:
    """A source document — a URL, a file path, or any opaque identifier
    in `source`, and the full text in `text`."""
    source: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """One chunk of a document.

    `chunk_index` is 0-based within the document; `source` and `doc_id`
    let the retriever cite the origin without keeping the whole document
    in memory.
    """
    chunk_id: str
    doc_id: str
    source: str
    chunk_index: int
    text: str


class Chunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_long_paragraph(self, para: str) -> List[str]:
        """Fallback: split a too-long paragraph on sentence boundaries."""
        sentences = _SENT_RE.split(para)
        out, current = [], ""
        for sent in sentences:
            if len(current) + len(sent) + 1 <= self.chunk_size:
                current = f"{current} {sent}".strip() if current else sent
            else:
                if current:
                    out.append(current)
                # Sentence still too long -> hard-wrap.
                while len(sent) > self.chunk_size:
                    out.append(sent[: self.chunk_size])
                    sent = sent[self.chunk_size - self.chunk_overlap:]
                current = sent
        if current:
            out.append(current)
        return out

    def chunk_document(self, doc: Document, doc_id: str) -> List[Chunk]:
        """Split one Document into a list of Chunks."""
        paragraphs = _PARA_RE.split(doc.text.strip())
        units: List[str] = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                units.append(para)
            else:
                units.extend(self._split_long_paragraph(para))

        # Greedy pack with overlap.
        chunks_text: List[str] = []
        current = ""
        for unit in units:
            sep = "\n\n" if current else ""
            candidate = f"{current}{sep}{unit}"
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks_text.append(current)
                    # Carry forward the overlap region.
                    current = current[-self.chunk_overlap:] + "\n\n" + unit \
                        if self.chunk_overlap > 0 else unit
                else:
                    chunks_text.append(unit)
                    current = ""
        if current:
            chunks_text.append(current)

        return [
            Chunk(
                chunk_id=f"{doc_id}#{i}",
                doc_id=doc_id,
                source=doc.source,
                chunk_index=i,
                text=text,
            )
            for i, text in enumerate(chunks_text)
        ]

    def chunk_corpus(self, docs: Sequence[Document]) -> List[Chunk]:
        out: List[Chunk] = []
        for i, doc in enumerate(docs):
            out.extend(self.chunk_document(doc, doc_id=f"doc_{i}"))
        return out
