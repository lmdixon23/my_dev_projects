# LLM Eval Harness

## Overview

**LLM_Eval_Harness** is a Python evaluation framework for LLM-based systems. You define cases in YAML or JSON, plug in any `respond_fn(prompt) -> str` callable (a RAG pipeline, an agent, a raw OpenAI call, a deterministic stub), and run them through four kinds of evaluators (exact match, regex, embedding similarity, LLM-as-judge). Results land in a self-contained HTML report you can ship as a CI artifact. Designed so the same harness grades the RAG assistant and the agent toolkit in this repo, or any other LLM system you want to ship safely.

## Key Features

- **Pluggable Responder**: `Runner(respond_fn, evaluators)` — the system under test is just a callable. Works for any pipeline, not just OpenAI.
- **Four Evaluators**: `ExactMatchEvaluator`, `RegexEvaluator` (with `must_not_contain` blocklist), `EmbeddingSimilarityEvaluator` (real sentence-transformers when installed, BoW cosine fallback otherwise), `LLMJudgeEvaluator` (1-5 grading via a judge model).
- **Single-File HTML Report**: Self-contained inline-CSS HTML. Upload as a CI artifact and view from any browser, no infra.
- **YAML or JSON Suites**: `load_cases("suite.yaml")` for human-friendly editing; same shape as JSON for tooling.
- **CI-Ready Exit Codes**: `python -m evals.cli` returns `0` on all-pass, `1` on any failure, `2` on invocation error — drop it straight into a GitHub Actions job.
- **Network-Free Tests**: All evaluator and runner tests use `httpx.MockTransport` and deterministic responder functions.

## Architecture

Standard Python package layout. Every evaluator implements the same `(passed, score, detail)` contract so adding a new evaluator (BLEU, ROUGE, latency-budget) requires writing one class.

```
evals/
  cases.py            Case, CaseResult, EvalRun + load_cases (YAML/JSON)
  evaluators.py       ExactMatch, Regex, EmbeddingSimilarity, LLMJudge
  runner.py           Apply a list of evaluators to a list of cases
  report.py           Single-file HTML report
  openai_respond.py   Convenience: an OpenAI-backed respond_fn
  cli.py              `python -m evals.cli --suite ... --report ...`
sample_suite.yaml     Demonstrates every evaluator at least once
smoke/run_smoke.py    End-to-end run with hardcoded responder + HTML report
tests/                Network-free tests
requirements.txt
.env.example
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Load**: Cases are loaded from a YAML or JSON file (the on-disk shape matches the `Case` dataclass field-for-field).
- **Respond**: For each case, the user-supplied `respond_fn(prompt)` is called.
- **Grade**: Each configured evaluator independently grades the response, returning `(passed, score, detail)`.
- **Aggregate**: Results are grouped by evaluator; pass rate and per-case scores are computed.
- **Report**: A standalone HTML page is written with a one-glance summary and a per-case results table.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- **OpenAI API Key** for `LLMJudgeEvaluator` and the bundled OpenAI responder; not required for `ExactMatchEvaluator`, `RegexEvaluator`, `EmbeddingSimilarityEvaluator`, or any custom `respond_fn`.

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/ai_engineering/llm_eval_harness
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY (only needed for the judge / OpenAI responder).
```

### Running

```bash
# Real run against an OpenAI model (uses every evaluator)
python -m evals.cli --suite sample_suite.yaml --report reports/eval_report.html

# Skip the judge if you want to avoid the extra API calls
python -m evals.cli --suite sample_suite.yaml --no-judge

# Smoke run: deterministic responder + BoW similarity, no API key required
python -m smoke.run_smoke
```

### Testing

```bash
python -m pytest tests/      # no network, no API key
```

## Technical Specifications

- **Language**: Python 3.10+
- **Suite Format**: YAML or JSON list of `{id, prompt, expected, expected_regex, must_not_contain, tags, metadata}`
- **Evaluator Contract**: `grade(case, response) -> (passed: bool, score: float in [0, 1], detail: str)`
- **Report Format**: Single self-contained HTML file (inline CSS, no JS)
- **Exit Codes**: `0` all-pass, `1` any-failure, `2` invocation-error
- **Test Coverage**: 11+ tests across 2 files; all evaluators network-free via `httpx.MockTransport` and dependency-injected embedders

## What This Project Demonstrates

- **Eval-first thinking**: this is the complement to the RAG and agent projects — you can't claim "production-shaped" without a way to measure regression. The harness here is exactly that.
- **A clean evaluator interface** (`Evaluator.grade`) that hides the differences between cheap string evaluators and expensive LLM-judge evaluators behind the same shape.
- **LLM-as-judge done responsibly**: deterministic prompt template, 0-temperature call, integer score parsing, clamped to a valid range, with a clear fallback when no API key is configured.
- **CI-friendly**: structured exit codes, single-file HTML report uploadable as an artifact, no external dashboards required to get value.
- **Pluggable system under test**: works against the `rag_assistant` project, the `agent_toolkit` project, a raw OpenAI call, a local model, or a deterministic stub — same harness, same report shape.

## Scope

- The LLM judge inherits the judge model's biases; it is not a substitute for human review on high-stakes evals.
- No bootstrap confidence intervals on pass rates — small suites can swing wildly between runs.
- No persistent run history; each invocation writes one HTML file. Add a SQLite log table if you want trend lines.
- `EmbeddingSimilarityEvaluator` falls back to a bag-of-words cosine when sentence-transformers isn't installed; the BoW score is rough.

## Future Enhancements

1. **Bootstrap CIs**: Resample case results to report pass-rate ± uncertainty. Scope flags that small suites swing between runs; this is the trust lever, so it leads.
2. **Judge Calibration Set**: Label a small set of responses by hand and report the LLM judge's agreement (Cohen's κ) against those labels. Directly answers the top Scope caveat — that the judge inherits the judge model's biases — instead of treating the judge as ground truth.
3. **Trend Storage**: Persist `EvalRun` summaries to SQLite so dashboards can plot pass rate over commits.
4. **Per-Tag Slicing**: Group results by `case.tags` in the report so regressions land in the right team's lap.
5. **More Evaluators**: BLEU, ROUGE, and exact-JSON match for structured outputs. (Dropped the earlier "ASR / transcription" item — category-mismatched for a text-output harness.)

## References

- Liang, P., et al. (2022). *Holistic Evaluation of Language Models (HELM).* arXiv:2211.09110.
- Zheng, L., et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685.
- Srivastava, A., et al. (2022). *Beyond the Imitation Game: Quantifying and Extrapolating the Capabilities of Language Models (BIG-bench).* arXiv:2206.04615.

## Contributing

Contributions are welcome. Open an issue first if you're planning a substantial change so we can align on scope.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
