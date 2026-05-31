"""Exercise the full agent loop using ScriptedLLM — no network calls."""

import unittest

from agent import Agent, ScriptedLLM
from agent.llm import LLMResponse
from agent.tools import ToolRegistry, tool


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@tool
def double(x: int) -> int:
    """Return 2 * x."""
    return x * 2


def _tc(call_id: str, name: str, args_json: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": args_json},
    }


class TestAgentLoop(unittest.TestCase):
    def setUp(self):
        self.reg = ToolRegistry()
        self.reg.register_many([add, double])

    def test_finishes_in_one_step_when_no_tool_needed(self):
        llm = ScriptedLLM([LLMResponse(content="42 is the answer.")])
        result = Agent(llm=llm, registry=self.reg).run("trivial question")
        self.assertEqual(result.answer, "42 is the answer.")
        self.assertEqual(result.stopped_for, "final")
        self.assertEqual(len(result.trace.tool_calls()), 0)

    def test_two_tool_calls_then_final(self):
        llm = ScriptedLLM([
            LLMResponse(content=None, tool_calls=[_tc("c1", "add", '{"a": 2, "b": 3}')]),
            LLMResponse(content=None, tool_calls=[_tc("c2", "double", '{"x": 5}')]),
            LLMResponse(content="The answer is 10."),
        ])
        result = Agent(llm=llm, registry=self.reg).run("compute (2+3)*2")
        self.assertEqual(result.answer, "The answer is 10.")
        self.assertEqual(result.stopped_for, "final")
        # The trace should show: tool_call add, tool_result add, tool_call double, tool_result double, final.
        self.assertEqual(len(result.trace.tool_calls()), 2)

    def test_unknown_tool_call_surfaces_to_trace_and_model_can_recover(self):
        llm = ScriptedLLM([
            LLMResponse(content=None, tool_calls=[_tc("c1", "no_such_tool", "{}")]),
            LLMResponse(content="Sorry, I'll stop calling that tool."),
        ])
        result = Agent(llm=llm, registry=self.reg).run("oops")
        self.assertEqual(result.stopped_for, "final")
        # The single tool call should have produced an error in the trace.
        tool_results = [s for s in result.trace.steps if s.kind == "tool_result"]
        self.assertEqual(len(tool_results), 1)
        self.assertFalse(tool_results[0].payload["ok"])

    def test_max_steps_guard(self):
        # Always asks for a tool, never gives a final answer.
        looping = [
            LLMResponse(content=None, tool_calls=[_tc(f"c{i}", "add", '{"a": 1, "b": 1}')])
            for i in range(20)
        ]
        llm = ScriptedLLM(looping)
        result = Agent(llm=llm, registry=self.reg, max_steps=3).run("loop forever")
        self.assertEqual(result.stopped_for, "max_steps")
        self.assertIsNone(result.answer)


if __name__ == "__main__":
    unittest.main()
