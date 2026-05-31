"""NLP Text Summarization CLI.

Calls the OpenAI Chat Completions REST API to summarize text. Features:
  * Async batch with concurrency limit (`--concurrency`).
  * Per-key rotation on rate-limit responses.
  * Exponential backoff using *asyncio.sleep* (not blocking time.sleep —
    the previous version blocked the event loop on every retry).
  * SQLite persistence of original text, summary, token usage, feedback.
  * Trend analysis: token totals, summary-length distribution,
    most-frequent content words.
  * File or stdin input (`--input-file`, `-`), not just interactive paste.

Environment:
  OPENAI_API_KEY        primary key, required
  OPENAI_API_KEY_2      optional secondary key, used for rotation on 429
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import re
import signal
import sqlite3
import sys
import time
from collections import Counter
from dataclasses import dataclass
from itertools import cycle
from typing import Iterator, List, Optional

import httpx
from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv

load_dotenv()
colorama_init(autoreset=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("summarizer")

DEFAULT_MODEL = "gpt-3.5-turbo"
AVAILABLE_MODELS = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o"]
LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French",
    "de": "German",  "zh": "Chinese", "ja": "Japanese",
}
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


# --------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------- #
def open_db(path: str = "summaries.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS summaries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            language TEXT NOT NULL,
            tokens_used INTEGER NOT NULL,
            original_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            feedback TEXT
        )"""
    )
    conn.commit()
    return conn


def save_summary(
    conn: sqlite3.Connection,
    *,
    model: str,
    language: str,
    tokens_used: int,
    original_text: str,
    summary: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO summaries(timestamp, model, language, tokens_used, original_text, summary)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (time.strftime("%Y-%m-%dT%H:%M:%S"), model, language, tokens_used, original_text, summary),
    )
    conn.commit()
    return cur.lastrowid


def save_feedback(conn: sqlite3.Connection, summary_id: int, feedback: str) -> None:
    conn.execute("UPDATE summaries SET feedback = ? WHERE id = ?", (feedback, summary_id))
    conn.commit()


# --------------------------------------------------------------------- #
# API client
# --------------------------------------------------------------------- #
@dataclass
class SummaryResult:
    summary: str
    tokens_used: int


class KeyRing:
    """Round-robin OpenAI API keys; supports manual rotation on 429."""

    def __init__(self, keys: List[Optional[str]]):
        cleaned = [k for k in keys if k]
        if not cleaned:
            raise RuntimeError(
                "No OpenAI API keys configured. Set OPENAI_API_KEY in env or .env."
            )
        self._keys = cleaned
        self._iter: Iterator[str] = cycle(self._keys)
        self.current: str = next(self._iter)

    def rotate(self) -> None:
        self.current = next(self._iter)


async def summarize_one(
    client: httpx.AsyncClient,
    text: str,
    *,
    model: str,
    language: str,
    max_tokens: int,
    keys: KeyRing,
    retries: int = 5,
) -> Optional[SummaryResult]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system",
             "content": f"You are a helpful assistant that summarizes text in "
                        f"{LANGUAGES.get(language, 'English')}."},
            {"role": "user", "content": f"Summarize the following text:\n\n{text}"},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.5,
    }
    for attempt in range(retries):
        try:
            r = await client.post(
                OPENAI_URL,
                headers={"Authorization": f"Bearer {keys.current}"},
                json=payload,
                timeout=30.0,
            )
            if r.status_code == 429:
                wait = 2 ** attempt
                log.warning("429 rate-limit, sleeping %ds (attempt %d/%d)", wait, attempt + 1, retries)
                keys.rotate()
                await asyncio.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            return SummaryResult(
                summary=data["choices"][0]["message"]["content"].strip(),
                tokens_used=int(data["usage"]["total_tokens"]),
            )
        except httpx.HTTPStatusError as exc:
            log.error("HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
            return None
        except httpx.RequestError as exc:
            log.error("network error: %s", exc)
            await asyncio.sleep(2 ** attempt)
    log.error("exhausted retries")
    return None


async def summarize_batch(
    texts: List[str],
    *,
    model: str,
    language: str,
    max_tokens: int,
    keys: KeyRing,
    concurrency: int,
) -> List[Optional[SummaryResult]]:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        async def _run(t: str) -> Optional[SummaryResult]:
            async with sem:
                return await summarize_one(
                    client, t, model=model, language=language,
                    max_tokens=max_tokens, keys=keys,
                )
        return await asyncio.gather(*[_run(t) for t in texts])


# --------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------- #
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "for", "on",
    "with", "as", "by", "this", "that", "be", "are", "was", "were", "has",
    "have", "had", "but", "from", "at", "not", "we", "you", "your", "they",
}


def analyze_summaries(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT tokens_used, summary FROM summaries").fetchall()
    if not rows:
        return {"count": 0}
    tokens = [r[0] for r in rows]
    lengths = [len(r[1].split()) for r in rows]
    word_counts: Counter = Counter()
    for _, summary in rows:
        for word in re.findall(r"[A-Za-z']+", summary.lower()):
            if word in STOPWORDS or len(word) < 3:
                continue
            word_counts[word] += 1
    return {
        "count": len(rows),
        "tokens_total": sum(tokens),
        "tokens_avg": sum(tokens) / len(tokens),
        "summary_words_avg": sum(lengths) / len(lengths),
        "summary_words_max": max(lengths),
        "summary_words_min": min(lengths),
        "top_words": word_counts.most_common(10),
    }


def render_analysis(stats: dict) -> str:
    if stats.get("count", 0) == 0:
        return "No summaries stored yet."
    lines = [
        f"Total summaries:        {stats['count']}",
        f"Total tokens used:      {stats['tokens_total']}",
        f"Tokens per summary avg: {stats['tokens_avg']:.1f}",
        f"Summary length (words): min {stats['summary_words_min']}, "
        f"avg {stats['summary_words_avg']:.1f}, max {stats['summary_words_max']}",
        "Top content words across all summaries:",
    ]
    for word, count in stats["top_words"]:
        lines.append(f"  {word:<18} {count}")
    return "\n".join(lines)


# --------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------- #
def read_texts(args: argparse.Namespace) -> List[str]:
    if args.input_file == "-":
        raw = sys.stdin.read()
        return [b.strip() for b in raw.split("\n\n") if b.strip()]
    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as fh:
            raw = fh.read()
        return [b.strip() for b in raw.split("\n\n") if b.strip()]
    print(Fore.CYAN + "Enter texts to summarize (one per prompt, blank line to finish):")
    out: List[str] = []
    while True:
        try:
            t = input("> ")
        except EOFError:
            break
        if not t.strip():
            break
        out.append(t)
    return out


def install_signal_handlers(conn: sqlite3.Connection) -> None:
    def _shutdown(_signum, _frame):
        print(Fore.RED + "\nReceived exit signal, closing DB.")
        with contextlib.suppress(Exception):
            conn.close()
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=AVAILABLE_MODELS)
    parser.add_argument("--language", default="en", choices=list(LANGUAGES.keys()))
    parser.add_argument("--max-tokens", type=int, default=150)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument(
        "--input-file", default=None,
        help="Path to a text file (blocks separated by blank lines), or '-' for stdin.",
    )
    parser.add_argument("--analyze", action="store_true", help="Print trend analysis and exit.")
    parser.add_argument("--db", default="summaries.db")
    args = parser.parse_args()

    conn = open_db(args.db)
    install_signal_handlers(conn)

    if args.analyze:
        print(render_analysis(analyze_summaries(conn)))
        conn.close()
        return

    try:
        keys = KeyRing([os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_KEY_2")])
    except RuntimeError as exc:
        print(Fore.RED + str(exc))
        conn.close()
        sys.exit(1)

    texts = read_texts(args)
    if not texts:
        print(Fore.YELLOW + "No texts provided; exiting.")
        conn.close()
        return

    print(Style.BRIGHT + Fore.BLUE +
          f"\nSummarizing {len(texts)} text(s) with {args.model} (concurrency={args.concurrency})...")
    results = asyncio.run(
        summarize_batch(
            texts,
            model=args.model,
            language=args.language,
            max_tokens=args.max_tokens,
            keys=keys,
            concurrency=args.concurrency,
        )
    )

    for i, (_text, result) in enumerate(zip(texts, results), start=1):
        if result is None:
            print(Fore.RED + f"\nSummary {i}: FAILED (see logs)")
            continue
        summary_id = save_summary(
            conn, model=args.model, language=args.language,
            tokens_used=result.tokens_used, original_text=_text, summary=result.summary,
        )
        print(Fore.GREEN + f"\nSummary {i} (id={summary_id}, tokens={result.tokens_used}):")
        print(result.summary)

    feedback_choice = input(Fore.CYAN + "\nProvide feedback on summaries? (y/N): ").strip().lower()
    if feedback_choice == "y":
        rows = conn.execute(
            "SELECT id FROM summaries ORDER BY id DESC LIMIT ?", (len(texts),)
        ).fetchall()
        for (sid,) in reversed(rows):
            fb = input(f"Feedback for summary {sid} (blank to skip): ").strip()
            if fb:
                save_feedback(conn, sid, fb)

    if input(Fore.CYAN + "\nShow trend analysis? (y/N): ").strip().lower() == "y":
        print(render_analysis(analyze_summaries(conn)))

    conn.close()


if __name__ == "__main__":
    main()
