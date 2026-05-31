"""Runner: applies a list of evaluators to each case.

The model that produces the responses is supplied as a `respond_fn(prompt) -> str`
callable. Keeping this as a callable instead of a hardcoded OpenAI client
means you can evaluate *any* system — a RAG pipeline, an agent, a local
LLM, even a deterministic rule engine — with the same harness.
"""

from __future__ import annotations

from typing import Callable, List

from .cases import Case, CaseResult, EvalRun
from .evaluators import Evaluator


RespondFn = Callable[[str], str]


class Runner:
    def __init__(self, respond_fn: RespondFn, evaluators: List[Evaluator]):
        if not evaluators:
            raise ValueError("Runner needs at least one evaluator")
        self.respond_fn = respond_fn
        self.evaluators = evaluators

    def run(self, suite_name: str, cases: List[Case]) -> EvalRun:
        run = EvalRun(suite_name=suite_name)
        for case in cases:
            response = self.respond_fn(case.prompt)
            for ev in self.evaluators:
                passed, score, detail = ev.grade(case, response)
                run.results.append(CaseResult(
                    case_id=case.id,
                    prompt=case.prompt,
                    response=response,
                    evaluator=ev.name,
                    passed=passed,
                    score=score,
                    detail=detail,
                ))
        return run
