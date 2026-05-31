"""Append-only trace of one agent run.

A `Trace` records each step the agent took — model thought, tool call,
tool result, final answer — in order. Three reasons this exists:

  1. Debugging: when an agent gets stuck or loops, the trace is the
     fastest way to see why.
  2. Eval / replay: traces can be diffed across runs to detect
     regressions in agent behavior.
  3. Observability: in production you ship traces to your logging
     pipeline so you can answer "what did this agent do last Tuesday?".
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal


StepKind = Literal["thought", "tool_call", "tool_result", "final"]


@dataclass
class TraceStep:
    kind: StepKind
    payload: Dict[str, Any]
    ts: float = field(default_factory=lambda: time.time())


@dataclass
class Trace:
    steps: List[TraceStep] = field(default_factory=list)

    # ---- record ----------------------------------------------------- #
    def thought(self, content: str) -> None:
        self.steps.append(TraceStep("thought", {"content": content}))

    def tool_call(self, name: str, arguments: Dict[str, Any]) -> None:
        self.steps.append(TraceStep("tool_call", {"name": name, "arguments": arguments}))

    def tool_result(self, name: str, output: Any, ok: bool, error: str | None) -> None:
        self.steps.append(TraceStep(
            "tool_result",
            {"name": name, "output": output, "ok": ok, "error": error},
        ))

    def final(self, content: str) -> None:
        self.steps.append(TraceStep("final", {"content": content}))

    # ---- query ------------------------------------------------------ #
    def __len__(self) -> int:
        return len(self.steps)

    def tool_calls(self) -> List[Dict[str, Any]]:
        return [s.payload for s in self.steps if s.kind == "tool_call"]

    def final_answer(self) -> str | None:
        for s in reversed(self.steps):
            if s.kind == "final":
                return str(s.payload["content"])
        return None

    # ---- io --------------------------------------------------------- #
    def to_json(self) -> str:
        return json.dumps([asdict(s) for s in self.steps], indent=2, default=str)

    def to_pretty(self) -> str:
        """Human-readable single-string rendering."""
        lines = []
        for i, s in enumerate(self.steps, 1):
            if s.kind == "thought":
                lines.append(f"[{i}] THOUGHT: {s.payload['content']}")
            elif s.kind == "tool_call":
                args = json.dumps(s.payload["arguments"], default=str)
                lines.append(f"[{i}] CALL    {s.payload['name']}({args})")
            elif s.kind == "tool_result":
                status = "ok" if s.payload["ok"] else f"ERR: {s.payload['error']}"
                out = str(s.payload["output"])
                if len(out) > 200:
                    out = out[:200] + "..."
                lines.append(f"[{i}] RESULT  ({status}) {out}")
            elif s.kind == "final":
                lines.append(f"[{i}] FINAL  {s.payload['content']}")
        return "\n".join(lines)
