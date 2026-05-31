"""ReAct-style agent loop.

Loop:
    1. Send conversation + tool specs to the LLM.
    2. If the LLM returns content (no tool call), record it as the final
       answer and exit.
    3. Otherwise, for each tool_call in the response:
         - dispatch through the registry
         - append the tool result back into the conversation
       Then go to step 1.
    4. Bail out at `max_steps` to prevent infinite loops.

The loop is deterministic given a deterministic LLM (the ScriptedLLM
used in tests is exactly this).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from .llm import BaseLLM, LLMMessage, LLMResponse
from .tools import ToolCall, ToolRegistry, ToolResult
from .trace import Trace


DEFAULT_SYSTEM = (
    "You are a helpful research assistant with access to tools. "
    "Always prefer calling a tool over guessing. When you have enough "
    "information to answer the user, respond with the final answer and "
    "stop calling tools."
)


@dataclass
class AgentResult:
    answer: Optional[str]
    trace: Trace
    stopped_for: str   # "final" | "max_steps" | "error"


class Agent:
    def __init__(
        self,
        llm: BaseLLM,
        registry: ToolRegistry,
        system_prompt: str = DEFAULT_SYSTEM,
        max_steps: int = 8,
    ):
        self.llm = llm
        self.registry = registry
        self.system_prompt = system_prompt
        self.max_steps = max_steps

    def run(self, user_message: str) -> AgentResult:
        trace = Trace()
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(role="user", content=user_message),
        ]
        specs = self.registry.specs()

        for _ in range(self.max_steps):
            response: LLMResponse = self.llm.chat(messages, specs)

            if response.content:
                trace.thought(response.content)
            if not response.wants_tool:
                trace.final(response.content or "")
                return AgentResult(answer=response.content, trace=trace, stopped_for="final")

            # Echo the assistant message (with its tool_calls) back into the convo.
            messages.append(LLMMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            ))

            for call in response.tool_calls:
                tc_id = call["id"]
                fn = call["function"]
                name = fn["name"]
                args_raw = fn.get("arguments") or "{}"
                try:
                    args = json.loads(args_raw)
                except json.JSONDecodeError:
                    args = {}
                trace.tool_call(name, args)
                result: ToolResult = self.registry.call(ToolCall(name=name, arguments=args))
                trace.tool_result(name, result.output, result.ok, result.error)
                content = json.dumps({"ok": result.ok, "output": result.output, "error": result.error},
                                     default=str)
                messages.append(LLMMessage(
                    role="tool", tool_call_id=tc_id, name=name, content=content,
                ))

        trace.final("(stopped: max_steps reached)")
        return AgentResult(answer=None, trace=trace, stopped_for="max_steps")
