"""Test-case format.

A `Case` is one input + the assertions an evaluator can check against it.
We deliberately keep `expected` loose (any string the case author wants)
because different evaluators interpret it differently — exact-match
treats it as a literal, regex treats it as a pattern, similarity treats
it as a reference text, the judge treats it as a description of what a
good answer looks like.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Case:
    id: str
    prompt: str
    expected: Optional[str] = None
    expected_regex: Optional[str] = None
    must_not_contain: Optional[List[str]] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseResult:
    case_id: str
    prompt: str
    response: str
    evaluator: str
    passed: bool
    score: float
    detail: str = ""


@dataclass
class EvalRun:
    suite_name: str
    results: List[CaseResult] = field(default_factory=list)

    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    def total(self) -> int:
        return len(self.results)

    def pass_rate(self) -> float:
        return self.passed() / self.total() if self.results else 0.0

    def grouped_by_evaluator(self) -> Dict[str, List[CaseResult]]:
        out: Dict[str, List[CaseResult]] = {}
        for r in self.results:
            out.setdefault(r.evaluator, []).append(r)
        return out


def load_cases(path: str) -> List[Case]:
    """Load cases from a YAML or JSON file. The on-disk shape is a list
    of objects with the same field names as `Case`."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as fh:
        if ext in (".yaml", ".yml"):
            import yaml
            raw = yaml.safe_load(fh) or []
        else:
            raw = json.load(fh)
    if not isinstance(raw, list):
        raise ValueError(f"{path}: expected a top-level list, got {type(raw).__name__}")
    return [Case(**item) for item in raw]
