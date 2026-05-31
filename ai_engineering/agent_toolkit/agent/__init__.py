"""Lightweight LLM agent toolkit.

Exports:
    tool                 - decorator that registers a Python function as a tool
    ToolRegistry         - holds registered tools, exposes JSON-schema specs
    ToolCall, ToolResult - structured records of one tool invocation
    Trace, TraceStep     - append-only record of an agent run
    Agent                - ReAct-style loop: model proposes a tool -> we run it -> repeat
    BaseLLM, OpenAILLM, ScriptedLLM
                         - LLM abstraction so tests can use a scripted stub instead
                           of a real OpenAI call.
"""

from .tools import tool, ToolRegistry, ToolCall, ToolResult, ToolError
from .trace import Trace, TraceStep
from .llm import BaseLLM, OpenAILLM, ScriptedLLM, LLMMessage
from .agent import Agent

__all__ = [
    "tool", "ToolRegistry", "ToolCall", "ToolResult", "ToolError",
    "Trace", "TraceStep",
    "BaseLLM", "OpenAILLM", "ScriptedLLM", "LLMMessage",
    "Agent",
]
