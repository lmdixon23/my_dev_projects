"""A `respond_fn` factory that calls the OpenAI Chat Completions API.

Kept separate from the rest of the library so the harness itself has
zero hard dependency on any specific model provider.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

import httpx

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def openai_respond_fn(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    client: Optional[httpx.Client] = None,
    system_prompt: str = "You are a concise, accurate assistant.",
    temperature: float = 0.0,
    max_tokens: int = 256,
) -> Callable[[str], str]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    def respond(prompt: str) -> str:
        c = client or httpx.Client(timeout=60.0)
        r = c.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    return respond
