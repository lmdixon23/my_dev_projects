"""LLM eval harness.

Exposes:
    Case, CaseResult, EvalRun       - dataclasses for test cases + outcomes
    load_cases                       - read cases from YAML or JSON
    Evaluator (Protocol)             - the contract every evaluator implements
    ExactMatchEvaluator              - case-folded string equality
    RegexEvaluator                   - matches `expected` (or `not_expected`) regex
    EmbeddingSimilarityEvaluator     - cosine similarity vs expected text
    LLMJudgeEvaluator                - prompts a judge model to grade the response
    Runner                           - applies a list of evaluators to each case
    HTMLReport                       - render an EvalRun to a standalone HTML file

The library is designed so a CI step can `python -m evals.cli --suite cases.yaml`
and produce a deterministic exit code (0 = all pass, 1 = failures).
"""

from .cases import Case, CaseResult, EvalRun, load_cases
from .evaluators import (
    Evaluator,
    ExactMatchEvaluator,
    RegexEvaluator,
    EmbeddingSimilarityEvaluator,
    LLMJudgeEvaluator,
)
from .runner import Runner
from .report import HTMLReport

__all__ = [
    "Case", "CaseResult", "EvalRun", "load_cases",
    "Evaluator", "ExactMatchEvaluator", "RegexEvaluator",
    "EmbeddingSimilarityEvaluator", "LLMJudgeEvaluator",
    "Runner", "HTMLReport",
]
