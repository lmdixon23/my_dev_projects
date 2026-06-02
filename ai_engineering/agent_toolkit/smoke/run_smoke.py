"""End-to-end smoke run using ScriptedLLM. No API key required.

Verifies that the agent loop can:
  1. Call a tool with structured arguments.
  2. Consume the tool result.
  3. Produce a final answer.

Writes the trace to reports/smoke_trace.md so a reviewer can see exactly
what happened.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from agent import Agent, ScriptedLLM
from agent.llm import LLMResponse
from builtin_tools import default_registry


def main() -> None:
    os.makedirs("reports", exist_ok=True)
    llm = ScriptedLLM([
        LLMResponse(
            content="I'll look up the definition of RAG, then compute 17 * 24.",
            tool_calls=[{
                "id": "tc1", "type": "function",
                "function": {"name": "keyword_lookup", "arguments": '{"query": "rag"}'},
            }],
        ),
        LLMResponse(
            content="Now the arithmetic.",
            tool_calls=[{
                "id": "tc2", "type": "function",
                "function": {"name": "calculator", "arguments": '{"expression": "17 * 24"}'},
            }],
        ),
        LLMResponse(
            content="RAG stands for Retrieval-Augmented Generation, and 17 * 24 = 408.",
        ),
    ])

    agent = Agent(llm=llm, registry=default_registry(), max_steps=5)
    result = agent.run("What does RAG mean, and what is 17 * 24?")

    report = (
        f"# Agent Toolkit — Smoke Run\n\n"
        f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_\n\n"
        f"**Stopped for:** {result.stopped_for}\n\n"
        f"**Tool calls:** {len(result.trace.tool_calls())}\n\n"
        f"## Final answer\n\n{result.answer}\n\n"
        f"## Trace\n\n```\n{result.trace.to_pretty()}\n```\n"
    )
    with open("reports/smoke_trace.md", "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"Wrote reports/smoke_trace.md  (stopped: {result.stopped_for}, "
          f"tool_calls: {len(result.trace.tool_calls())})")


if __name__ == "__main__":
    main()
