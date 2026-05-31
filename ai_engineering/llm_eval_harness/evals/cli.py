"""Run a YAML/JSON eval suite end-to-end.

Usage:
    # Real model under test
    python -m evals.cli --suite sample_suite.yaml --report report.html

    # Skip the LLM judge (faster, no extra API calls)
    python -m evals.cli --suite sample_suite.yaml --no-judge

Exit codes:
    0  every case passed every evaluator
    1  at least one failure
    2  invocation error
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from .cases import load_cases
from .evaluators import (
    EmbeddingSimilarityEvaluator,
    ExactMatchEvaluator,
    LLMJudgeEvaluator,
    RegexEvaluator,
)
from .openai_respond import openai_respond_fn
from .report import HTMLReport
from .runner import Runner


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suite", required=True, help="YAML or JSON file of cases")
    parser.add_argument("--suite-name", default=None)
    parser.add_argument("--report", default="reports/eval_report.html")
    parser.add_argument("--no-exact", action="store_true")
    parser.add_argument("--no-regex", action="store_true")
    parser.add_argument("--no-similarity", action="store_true")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--similarity-threshold", type=float, default=0.6)
    parser.add_argument("--judge-threshold", type=float, default=0.6)
    args = parser.parse_args()

    try:
        cases = load_cases(args.suite)
    except (FileNotFoundError, ValueError) as exc:
        print(f"could not load suite: {exc}", file=sys.stderr)
        sys.exit(2)

    evaluators = []
    if not args.no_exact:
        evaluators.append(ExactMatchEvaluator())
    if not args.no_regex:
        evaluators.append(RegexEvaluator())
    if not args.no_similarity:
        evaluators.append(EmbeddingSimilarityEvaluator(threshold=args.similarity_threshold))
    if not args.no_judge:
        evaluators.append(LLMJudgeEvaluator(threshold=args.judge_threshold))
    if not evaluators:
        print("no evaluators enabled", file=sys.stderr)
        sys.exit(2)

    try:
        respond_fn = openai_respond_fn()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    runner = Runner(respond_fn=respond_fn, evaluators=evaluators)
    suite_name = args.suite_name or os.path.basename(args.suite)
    run = runner.run(suite_name, cases)

    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    HTMLReport.write(run, args.report)
    print(f"{run.passed()}/{run.total()} passed ({run.pass_rate()*100:.1f}%) -> {args.report}")
    sys.exit(0 if run.passed() == run.total() else 1)


if __name__ == "__main__":
    main()
