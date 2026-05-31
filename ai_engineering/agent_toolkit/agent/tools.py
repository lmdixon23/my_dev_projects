"""Typed tool registry.

`@tool` decorates a Python function with a docstring and type-hinted
arguments and registers it as something the agent can call. The
registry derives a JSON-schema spec for each tool that's compatible
with the OpenAI Chat Completions tool-call format.

Tool implementations should be deterministic and side-effect-free
when possible. For tools that *do* have side effects (file write,
shell exec), gate them behind an explicit `safe_mode=False` flag so
the agent's default behavior is read-only.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, get_type_hints


# --------------------------------------------------------------------- #
# Public dataclasses
# --------------------------------------------------------------------- #
@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    name: str
    arguments: Dict[str, Any]
    output: Any
    ok: bool = True
    error: Optional[str] = None


class ToolError(Exception):
    """Raised by a tool to signal a domain error the agent should see."""


# --------------------------------------------------------------------- #
# Decorator + registry
# --------------------------------------------------------------------- #
_PY_TO_JSON_TYPE = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _schema_for(func: Callable[..., Any]) -> Dict[str, Any]:
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    properties: Dict[str, Dict[str, Any]] = {}
    required: List[str] = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        py_type = hints.get(name, str)
        json_type = _PY_TO_JSON_TYPE.get(py_type, "string")
        prop: Dict[str, Any] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            prop["default"] = param.default
        properties[name] = prop
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def tool(_func: Optional[Callable[..., Any]] = None,
         *,
         name: Optional[str] = None,
         description: Optional[str] = None) -> Callable[..., Any]:
    """Decorator that tags a function as a tool. Description defaults to
    the first paragraph of the docstring."""

    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        fn._tool_name = name or fn.__name__  # type: ignore[attr-defined]
        doc = (description or fn.__doc__ or "").strip().split("\n\n")[0]
        fn._tool_description = doc.strip()    # type: ignore[attr-defined]
        fn._tool_schema = _schema_for(fn)     # type: ignore[attr-defined]
        return fn

    return wrap(_func) if _func is not None else wrap


@dataclass
class ToolRegistry:
    tools: Dict[str, Callable[..., Any]] = field(default_factory=dict)

    def register(self, fn: Callable[..., Any]) -> None:
        if not hasattr(fn, "_tool_name"):
            raise ValueError(f"{fn.__name__} is not decorated with @tool")
        self.tools[fn._tool_name] = fn  # type: ignore[attr-defined]

    def register_many(self, fns: List[Callable[..., Any]]) -> None:
        for fn in fns:
            self.register(fn)

    def specs(self) -> List[Dict[str, Any]]:
        """OpenAI-compatible tool specs."""
        out: List[Dict[str, Any]] = []
        for fn in self.tools.values():
            out.append({
                "type": "function",
                "function": {
                    "name": fn._tool_name,                # type: ignore[attr-defined]
                    "description": fn._tool_description,  # type: ignore[attr-defined]
                    "parameters": fn._tool_schema,        # type: ignore[attr-defined]
                },
            })
        return out

    def call(self, call: ToolCall) -> ToolResult:
        fn = self.tools.get(call.name)
        if fn is None:
            return ToolResult(call.name, call.arguments, output=None, ok=False,
                              error=f"unknown tool '{call.name}'")
        try:
            output = fn(**call.arguments)
        except ToolError as exc:
            return ToolResult(call.name, call.arguments, output=None, ok=False, error=str(exc))
        except TypeError as exc:
            return ToolResult(call.name, call.arguments, output=None, ok=False,
                              error=f"bad arguments to {call.name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - surface to model for recovery
            return ToolResult(call.name, call.arguments, output=None, ok=False,
                              error=f"{type(exc).__name__}: {exc}")
        return ToolResult(call.name, call.arguments, output=output, ok=True)

    def __len__(self) -> int:
        return len(self.tools)
