"""A small set of built-in tools.

These exist so the demo CLI and tests can exercise the agent loop without
the user having to write tools themselves. Real deployments will replace
or extend this set.

Every tool here is **read-only** or pure — no file writes, no shell exec.
Anything destructive should require an explicit `safe_mode=False` flag.
"""

from __future__ import annotations

import ast
import math
import operator
import os
from typing import Dict, List

from agent.tools import ToolError, ToolRegistry, tool


# --------------------------------------------------------------------- #
# Safe arithmetic evaluator (AST allowlist, no eval())
# --------------------------------------------------------------------- #
# Instead of `eval()` behind a character whitelist, we parse the expression
# to an AST and walk it with an explicit allowlist of node types, operators,
# functions, and constants. Anything outside the allowlist (names, attribute
# access, subscripts, calls to non-whitelisted functions, comprehensions,
# etc.) raises ToolError. This makes the safety property structural rather
# than dependent on string filtering.
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "log": math.log, "exp": math.exp,
}
_NAMES = {"pi": math.pi, "e": math.e}


def _eval_ast(node: ast.AST) -> float:
    """Recursively evaluate an allowlisted arithmetic AST node."""
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ToolError(f"disallowed constant: {node.value!r}")
        return node.value
    if isinstance(node, ast.BinOp):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise ToolError(f"disallowed operator: {type(node.op).__name__}")
        return op(_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _UNARYOPS.get(type(node.op))
        if op is None:
            raise ToolError(f"disallowed unary operator: {type(node.op).__name__}")
        return op(_eval_ast(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
            raise ToolError("disallowed function call")
        if node.keywords:
            raise ToolError("keyword arguments are not allowed")
        return _FUNCS[node.func.id](*[_eval_ast(a) for a in node.args])
    if isinstance(node, ast.Name):
        if node.id in _NAMES:
            return _NAMES[node.id]
        raise ToolError(f"disallowed name: {node.id}")
    raise ToolError(f"disallowed syntax: {type(node).__name__}")


@tool
def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression. Allowed: numbers, + - * / // % **,
    parentheses, and the functions sqrt, sin, cos, log, exp plus constants pi, e.
    Names, attribute access, and any other call are rejected (no eval())."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ToolError(f"could not parse expression: {expression!r} ({exc})")
    try:
        return float(_eval_ast(tree))
    except ToolError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface to agent
        raise ToolError(f"could not evaluate expression: {exc}")


@tool
def list_directory(path: str = ".") -> List[str]:
    """List the entries in a directory (sorted, non-recursive). Returns up to 200 names."""
    if not os.path.isdir(path):
        raise ToolError(f"not a directory: {path}")
    return sorted(os.listdir(path))[:200]


@tool
def read_file(path: str, max_chars: int = 2000) -> str:
    """Return the first `max_chars` characters of a UTF-8 text file."""
    if not os.path.isfile(path):
        raise ToolError(f"not a file: {path}")
    if os.path.getsize(path) > 10 * 1024 * 1024:
        raise ToolError("file too large (>10 MB)")
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read(max_chars)


@tool
def keyword_lookup(query: str) -> Dict[str, str]:
    """Look up a built-in glossary of AI/engineering terms. Demo stand-in for a
    real knowledge-base or web-search tool."""
    glossary = {
        "rag": ("Retrieval-Augmented Generation: ground LLM answers in retrieved "
                "documents instead of relying only on parametric memory."),
        "react": ("ReAct: an agent pattern that alternates between Thought and "
                  "Action steps so the model can use tools mid-reasoning."),
        "embedding": "A dense vector representation of a piece of text or other input.",
        "faiss": "A library from Meta for efficient nearest-neighbor search over dense vectors.",
        "hnsw": "Hierarchical Navigable Small World: a fast approximate-NN graph index.",
    }
    key = query.lower().strip()
    if key not in glossary:
        return {"found": "false", "matches": ", ".join(sorted(glossary.keys()))}
    return {"found": "true", "term": key, "definition": glossary[key]}


def default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_many([calculator, list_directory, read_file, keyword_lookup])
    return reg
