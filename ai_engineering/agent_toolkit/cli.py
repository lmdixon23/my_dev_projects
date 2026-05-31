"""Agent Toolkit CLI.

Usage:
    python cli.py "What is 17 * 24, and what does RAG stand for?"
    python cli.py "List the files in this directory." --verbose
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from agent import Agent
from agent.llm import OpenAILLM
from builtin_tools import default_registry


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the demo agent on a single user message.")
    parser.add_argument("message", nargs="+", help="user message")
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--verbose", action="store_true", help="print full trace")
    args = parser.parse_args()

    try:
        llm = OpenAILLM()
    except RuntimeError as exc:
        sys.exit(str(exc))

    agent = Agent(llm=llm, registry=default_registry(), max_steps=args.max_steps)
    result = agent.run(" ".join(args.message))

    if args.verbose:
        print(result.trace.to_pretty())
        print("---")
    print(result.answer or "(no answer)")
    print(f"\n[stopped: {result.stopped_for}, steps={len(result.trace)}, "
          f"tool_calls={len(result.trace.tool_calls())}]")


if __name__ == "__main__":
    main()
