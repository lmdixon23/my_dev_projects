"""End-to-end smoke run using a hardcoded responder. No API key required.

Exercises ExactMatch + Regex + EmbeddingSimilarity (BoW fallback) +
LLMJudge (skipped via no_api_key path). Writes reports/smoke_eval.html.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from evals.cases import Case
from evals.evaluators import (
    EmbeddingSimilarityEvaluator,
    ExactMatchEvaluator,
    LLMJudgeEvaluator,
    RegexEvaluator,
)
from evals.report import HTMLReport
from evals.runner import Runner


def _fake_respond(prompt: str) -> str:
    if "capital of France" in prompt:
        return "Paris"
    if "year between 2020 and 2030" in prompt:
        return "The year I'm picking is 2024."
    if "monarch of Mars" in prompt:
        return "Mars has no monarch; the question is unanswerable as posed."
    if "Define retrieval-augmented generation" in prompt:
        return ("Retrieval-augmented generation grounds language model output "
                "in passages retrieved from a corpus instead of relying on "
                "parametric memory.")
    return "I don't know."


def main() -> None:
    os.makedirs("reports", exist_ok=True)
    cases = [
        Case(id="c1", prompt="What is the capital of France? Answer with just the city.",
             expected="Paris"),
        Case(id="c2", prompt="Mention any year between 2020 and 2030 in your answer.",
             expected_regex=r"20(2[0-9]|30)"),
        Case(id="c3", prompt="Without inventing, who is the current monarch of Mars?",
             must_not_contain=["the current monarch is", "Mars is ruled"]),
        Case(id="c4", prompt="Define retrieval-augmented generation in one sentence.",
             expected="Retrieval-augmented generation grounds language model output in retrieved documents."),
    ]
    evaluators = [
        ExactMatchEvaluator(),
        RegexEvaluator(),
        EmbeddingSimilarityEvaluator(threshold=0.3, embed_fn=lambda _t: None),
        LLMJudgeEvaluator(api_key=None),  # disabled by missing key; shows up as fail in report
    ]
    run = Runner(_fake_respond, evaluators).run("smoke", cases)
    out_path = "reports/smoke_eval.html"
    HTMLReport.write(run, out_path)
    print(f"{run.passed()}/{run.total()} passed -> {out_path}  ({datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z)")


if __name__ == "__main__":
    main()
