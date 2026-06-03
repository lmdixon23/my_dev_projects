# Agent Toolkit

## Overview

**Agent_Toolkit** is a Python library for building ReAct-style LLM agents with structured tool use. A `@tool` decorator registers Python functions as callable tools; an `Agent` orchestrates the model -> tool -> result loop; a `Trace` records every step for debugging, eval, and observability. Because the LLM sits behind a small `BaseLLM` interface, tests run end-to-end against a `ScriptedLLM` stub with no network or API key required.

## Key Features

- **Typed Tool Registry**: `@tool`-decorated Python functions get auto-derived JSON schemas from their type hints. The registry emits OpenAI-compatible tool specs and dispatches calls with structured-error reporting.
- **ReAct-Style Loop**: The `Agent` alternates between LLM proposals and tool execution until the model returns a final answer or `max_steps` is hit (anti-loop guard).
- **Append-Only Trace**: `Trace` records each `thought / tool_call / tool_result / final` step with timestamps; `to_pretty()` and `to_json()` render it for logs or eval pipelines.
- **Pluggable LLM Interface**: `BaseLLM` is the only thing the agent depends on. `OpenAILLM` calls the real Chat Completions tool-use API; `ScriptedLLM` replays a list of canned responses so tests are deterministic and network-free.
- **Safe-by-Default Built-in Tools**: `calculator`, `list_directory`, `read_file`, `keyword_lookup`. All read-only or pure; arithmetic tool whitelist-validates input characters to block `__import__` style abuse.

## Architecture

Standard Python package layout. The agent loop knows nothing about specific tools or specific LLM providers — both are dependency-injected.

```
agent/
  tools.py       @tool decorator, ToolRegistry, ToolCall/ToolResult
  trace.py       Trace + TraceStep (append-only)
  llm.py         BaseLLM, OpenAILLM, ScriptedLLM, LLMMessage, LLMResponse
  agent.py       ReAct loop with max_steps guard
builtin_tools.py 4 safe-by-default tools + default_registry()
cli.py           Single-message demo (uses OpenAILLM)
smoke/run_smoke.py  End-to-end ScriptedLLM run -> reports/smoke_trace.md
tests/           Network-free tests (ScriptedLLM, pure unit tests)
requirements.txt
.env.example
```

## Example Usage

Each agent run follows the same sequence:

- **Registration**: Python functions are registered as tools and the registry produces JSON-schema specs the LLM can see.
- **Inference**: The agent sends the conversation + tool specs to the LLM, which either answers or proposes a tool call with structured arguments.
- **Dispatch**: The agent dispatches each proposed call through the registry, captures the result (or structured error), and appends it back to the conversation as a `role=tool` message.
- **Termination**: When the model returns a non-empty `content` and no `tool_calls`, the agent records that as the final answer and exits. If the model gets stuck in a loop, `max_steps` cuts it off.
- **Tracing**: Every step is recorded in a `Trace` that can be rendered for logs, diffed across runs, or shipped to an observability pipeline.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- **OpenAI API Key** for the production `OpenAILLM`; not needed for tests or the smoke run.

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/ai_engineering/agent_toolkit
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY.
```

### Running

```bash
# Real run against OpenAI
python cli.py "What is 17 * 24, and what does RAG stand for?" --verbose

# Smoke run, no API key required, writes reports/smoke_trace.md
python -m smoke.run_smoke
```

### Testing

```bash
python -m pytest tests/      # no network, no API key
```

## Technical Specifications

- **Language**: Python 3.10+
- **LLM Interface**: `BaseLLM.chat(messages, tool_specs) -> LLMResponse`; the only contract a new provider has to implement.
- **Tool Spec Format**: OpenAI Chat Completions function-tool format (`{"type": "function", "function": {...}}`).
- **Loop Termination**: First non-tool response wins; `max_steps` (default 8) bounds runaway loops.
- **Tracing**: append-only `Trace` with `to_pretty()` (human) and `to_json()` (machine) renderings.
- **Test Coverage**: 9 tests across 2 files using `ScriptedLLM`; no network or model download required.

## What This Project Demonstrates

- A **clean dependency-injection seam** for the LLM. The agent is testable end-to-end with a 30-line stub instead of a mocked-out OpenAI client.
- Idiomatic **typed-tool registration**: Python type hints flow into JSON schemas via `inspect.get_type_hints`, so the schema and the function signature can never drift apart.
- A **`max_steps` guard** as a first-class loop-termination rule. It's the simplest defense against the most common agent failure mode: infinite tool-call loops.
- **Structured error surfacing** through `ToolResult`: tool errors are visible to the model in the next turn so it can self-recover instead of crashing the agent.
- **Append-only Trace as observability primitive**: ships with `to_pretty()` for humans and `to_json()` for machines. That's the shape you'll want when agents need proper observability.

## Scope

- No streaming responses. The agent reads each LLM response in full before deciding the next step.
- No parallel tool calls. The OpenAI API supports it; the loop here is strictly sequential. Adding parallel dispatch is a ~20-line change but increases tool-side complexity around shared state.
- No memory / scratchpad beyond the conversation itself; long sessions will eventually hit context-window limits.
- The included `calculator` parses expressions to an AST and evaluates them against an explicit node/operator/function allowlist — no `eval()`. It covers the demo operator set; it is intentionally not a general expression engine.

## Future Enhancements

1. **Parallel Tool Calls**: Dispatch multiple `tool_calls` in one model turn via `asyncio.gather`.
2. **Memory**: Persistent conversation memory with summarization-on-overflow.
3. **Provider Pluralism**: Add `AnthropicLLM` / `LocalLlamaLLM` alongside the current `OpenAILLM` and `ScriptedLLM` implementations of `BaseLLM` (see `agent/llm.py`).
4. **Trace Shipping**: Wire `Trace` into OpenTelemetry spans for production observability.

> **Implemented** — _AST-safe calculator_: the `eval()`-after-whitelist in `builtin_tools.py` was replaced with an `ast.parse` + node-allowlist evaluator (no `eval()`); `tests/test_tools.py` covers precedence, whitelisted functions, and rejection of attribute access / unknown names. Verified: `pytest` reports 14/14 passing.

## References

- Yao, S., et al. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models.* arXiv:2210.03629.
- Schick, T., et al. (2023). *Toolformer: Language Models Can Teach Themselves to Use Tools.* arXiv:2302.04761.

Licensed under the [MIT License](https://github.com/lmdixon23/my_dev_projects/blob/main/LICENSE).
