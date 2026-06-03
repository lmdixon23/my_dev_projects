# NLP Text Summarization CLI

## Overview

**NLP_Text_Summarization_CLI** is a Python command-line tool that summarizes text via the OpenAI Chat Completions API. It handles async batching with a controllable concurrency limit, exponential backoff with per-key rotation on 429s, SQLite persistence of every summary plus token usage and feedback, real trend analysis over stored summaries (token totals, length distributions, top non-stopword content terms), and file / stdin input modes. The test suite is tokenizer-free and network-free, covering the HTTP retry path via `httpx.MockTransport`.

## Key Features

- **Intelligent Rate Limiting**: On a 429 response, the client rotates to the next API key and waits `2^attempt` seconds via **`asyncio.sleep`** (the original used blocking `time.sleep`, which stalled the entire event loop).
- **Batch Request Optimization**: `asyncio.gather` over all input texts gated by an `asyncio.Semaphore(args.concurrency)` so the batch doesn't self-DDOS the API.
- **API Key Rotation**: `KeyRing` cycles between `OPENAI_API_KEY` and `OPENAI_API_KEY_2`; raises a clear error if no keys are configured (instead of silently sending `Bearer None`).
- **User Feedback Integration**: Per-summary feedback is stored against the summary row in SQLite for later analysis.
- **Advanced Data Analysis**: `--analyze` walks every stored summary and reports total / average tokens, summary-length distribution (min / avg / max words), and top non-stopword content terms across all summaries.
- **Flexible Input**: Interactive prompt, `--input-file <path>` (blocks separated by blank lines), or `--input-file -` (read from stdin).
- **Modern Models**: `gpt-3.5-turbo`, `gpt-4o-mini`, `gpt-4o`.

## Architecture

Single-file CLI plus a `tests/` directory. The HTTP path is the only side-effectful surface; everything else (persistence, analysis, key rotation) is pure and easy to test.

```
main.py                  Single-file CLI: KeyRing, summarize_one, summarize_batch,
                         analyze_summaries, render_analysis, run_cli.
requirements.txt         httpx, python-dotenv, colorama
.env.example             OPENAI_API_KEY contract
sample_inputs.txt        Three real paragraphs for --input-file smoke runs
tests/
  test_main.py           7 tests: KeyRing, persistence + analysis,
                         summarize_one happy-path via MockTransport,
                         429 -> rotate -> retry succeeds via MockTransport
```

## Example Usage

A typical run looks like this:

- **Input Text**: Provide text via interactive prompt, file, or stdin.
- **API Request**: The application sends each text to the OpenAI API for summarization, throttled by the configured concurrency.
- **Summary Generation**: Each response is parsed for `summary` and `tokens_used`, persisted to SQLite, and printed.
- **User Feedback**: Optionally, the user provides feedback per summary which is stored in the same row.
- **Analysis**: Optionally, the user (or `--analyze`) prints token-usage totals, length stats, and a top-words histogram across all stored summaries.

## Getting Started

### Prerequisites

- **Python 3.10+**.
- **OpenAI API Key**. Sign up at [platform.openai.com](https://platform.openai.com).

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/ai_engineering/nlp_text_summarization_api
python -m venv venv
# Windows: venv\Scripts\activate    /    macOS / Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Then edit .env and set OPENAI_API_KEY (and optionally OPENAI_API_KEY_2).
```

### Running

```bash
# Summarize a file with controlled concurrency
python main.py --input-file sample_inputs.txt --concurrency 3 --max-tokens 80

# Pipe text in from stdin
cat README.md | python main.py --input-file - --max-tokens 120

# Standalone trend analysis over everything previously summarized
python main.py --analyze
```

### Testing

```bash
# No network or API key needed; HTTP path is exercised via httpx.MockTransport.
python -m unittest discover tests
```

## Technical Specifications

- **Language**: Python 3.10+
- **HTTP Client**: `httpx.AsyncClient` (async)
- **Concurrency Control**: `asyncio.Semaphore(args.concurrency)`
- **Retry / Backoff**: Exponential `await asyncio.sleep(2 ** attempt)` with key rotation on 429
- **Persistence**: SQLite with columns for timestamp, model, language, tokens used, original text, summary, feedback
- **Test Coverage**: 7 tests across one file, no network / no API key required (uses `httpx.MockTransport`)
- **Config**: `.env` via `python-dotenv` (`OPENAI_API_KEY`, `OPENAI_API_KEY_2`)

## What This Project Demonstrates

- Knowing **why `time.sleep` inside `async def` is a real bug** and how to fix it with `asyncio.sleep`.
- **Concurrency control via `asyncio.Semaphore`**: the right primitive for "fan out but only N in flight at once".
- A **clean key-rotation abstraction** with explicit "no key configured" error handling.
- **Testable HTTP code**: using `httpx.MockTransport` to assert the 429 -> rotate -> retry -> success path without any real network call.
- **Real analytical output** from stored data (token totals, length distributions, top non-stopword terms) instead of the previous `print(rows)` stub.
- File + stdin input modes, so the tool composes with other CLI tools (`cat file | python main.py --input-file -`).

## Scope

- The README's longer "Future Enhancements" list (GUI, voice I/O, CMS plugins, mobile, end-to-end encryption) remains aspirational — the rewrite focused on making the *baseline* CLI behave the way the README's "Key Features" block describes.
- API-key rotation is reactive (rotates on 429) and not stateful across sessions; real rotation logic would persist per-key usage in the DB to balance load proactively.
- No retry budget across the whole batch — each request retries up to `--retries` independently.

## Future Enhancements

1. **Stateful Key Rotation**: Persist per-key quota usage and route the next request to the least-used key. Closes the Scope note that rotation is currently reactive-only (`main.py` rotates on 429).
2. **Batch Retry Budget**: Add a shared retry/back-off budget across a batch instead of each request retrying independently up to `--retries`. Directly addresses the Scope gap.
3. **Extractive-Baseline ROUGE Comparison**: Score the LLM summaries against a cheap extractive baseline (e.g. lead-3 / TextRank) with ROUGE on a small set, so the project reports a summarization quality number rather than only demonstrating the pipeline.
4. **Contextual Summarization**: Pass user-provided keywords / focus areas into the system prompt.
5. **Streaming Output**: Use the streaming Chat Completions endpoint so users see summaries token-by-token.
6. **Cross-Platform GUI**: Wrap the CLI in a small Electron or Tauri shell. (Lowest priority — app-shell work, aspirational per Scope.)

## References

- OpenAI. *Chat Completions API Reference.* https://platform.openai.com/docs/api-reference/chat
- Liu, Y., & Lapata, M. (2019). *Text Summarization with Pretrained Encoders.* arXiv:1908.08345.

Licensed under the [MIT License](https://github.com/lmdixon23/my_dev_projects/blob/main/LICENSE).
