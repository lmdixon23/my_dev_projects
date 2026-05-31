"""LLM abstraction.

The agent only depends on `BaseLLM.chat(messages, tool_specs)` returning
a structured `LLMResponse`. Two concrete implementations:

  * `OpenAILLM`: calls the real OpenAI Chat Completions tool-use API.
  * `ScriptedLLM`: replays a list of pre-recorded responses. Used by
    tests so the agent loop is exercised end-to-end without any network
    call or API key.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@dataclass
class LLMMessage:
    role: str
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    name: Optional[str] = None

    def to_openai(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role}
        if self.content is not None:
            d["content"] = self.content
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        if self.name is not None:
            d["name"] = self.name
        return d


@dataclass
class LLMResponse:
    content: Optional[str]
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def wants_tool(self) -> bool:
        return bool(self.tool_calls)


class BaseLLM:
    def chat(self, messages: List[LLMMessage], tool_specs: List[Dict[str, Any]]) -> LLMResponse:
        raise NotImplementedError


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        temperature: float = 0.0,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = client
        self.temperature = temperature

    def chat(self, messages: List[LLMMessage], tool_specs: List[Dict[str, Any]]) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        client = self._client or httpx.Client(timeout=60.0)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_openai() for m in messages],
            "temperature": self.temperature,
        }
        if tool_specs:
            payload["tools"] = tool_specs
            payload["tool_choice"] = "auto"
        r = client.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        msg = data["choices"][0]["message"]
        return LLMResponse(
            content=msg.get("content"),
            tool_calls=msg.get("tool_calls") or [],
            raw=data,
        )


class ScriptedLLM(BaseLLM):
    """Replays a list of LLMResponse objects in order. Used by tests."""

    def __init__(self, responses: List[LLMResponse]):
        self._responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    def chat(self, messages: List[LLMMessage], tool_specs: List[Dict[str, Any]]) -> LLMResponse:
        self.calls.append({
            "messages": [m.to_openai() for m in messages],
            "tool_specs": tool_specs,
        })
        if not self._responses:
            raise RuntimeError("ScriptedLLM ran out of canned responses.")
        return self._responses.pop(0)
