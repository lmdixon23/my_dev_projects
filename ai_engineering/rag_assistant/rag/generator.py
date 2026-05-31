"""Calls the OpenAI Chat Completions API with the retrieved context.

The generator is intentionally minimal — most of the value in a RAG
system comes from the retriever, not the prompt template. Two things
this module gets right that homemade implementations often miss:

  1. **Cite the sources.** The prompt instructs the model to cite the
     `source` of each chunk it relies on, and the returned dict includes
     the sources separately so a UI can show "this answer came from X".
  2. **Refuse on empty retrieval.** If no chunks are retrieved, the
     generator returns a "no context" response instead of letting the
     model hallucinate. This is the single most common RAG failure mode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Sequence

import httpx

from .retriever import RetrievedChunk

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are a careful research assistant. Answer the user's question using "
    "only the provided context. If the context does not contain enough "
    "information, say so. Cite the source of any claim in square brackets, "
    "e.g. [source: foo.md]. Do not invent sources."
)


@dataclass
class GenerationResult:
    answer: str
    sources: List[str]
    tokens_used: int


def format_context(chunks: Sequence[RetrievedChunk]) -> str:
    blocks = []
    for r in chunks:
        blocks.append(
            f"[source: {r.chunk.source}#{r.chunk.chunk_index} "
            f"score={r.score:.3f}]\n{r.chunk.text}"
        )
    return "\n\n---\n\n".join(blocks)


class Generator:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = client

    def _post(self, payload: dict) -> dict:
        client = self._client or httpx.Client(timeout=60.0)
        r = client.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        r.raise_for_status()
        return r.json()

    def generate(
        self,
        question: str,
        retrieved: Sequence[RetrievedChunk],
        *,
        max_tokens: int = 400,
        temperature: float = 0.2,
    ) -> GenerationResult:
        if not retrieved:
            return GenerationResult(
                answer=("I could not find any relevant context in the indexed "
                        "documents to answer that question."),
                sources=[],
                tokens_used=0,
            )
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set; cannot call the generation model."
            )

        context = format_context(retrieved)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",
                 "content": f"Context:\n\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = self._post(payload)
        return GenerationResult(
            answer=data["choices"][0]["message"]["content"].strip(),
            sources=sorted({r.chunk.source for r in retrieved}),
            tokens_used=int(data["usage"]["total_tokens"]),
        )
