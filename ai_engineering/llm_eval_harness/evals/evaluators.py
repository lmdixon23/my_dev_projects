"""Concrete evaluator implementations.

All evaluators implement the `Evaluator` protocol:
    grade(case, response) -> (passed: bool, score: float, detail: str)

Scores are in [0, 1]. `passed` is the boolean version (typically
`score >= threshold`). Keeping these separate lets a CI step use `passed`
for gating while a dashboard uses `score` for trend analysis.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Protocol, Tuple

import httpx

from .cases import Case


class Evaluator(Protocol):
    name: str
    def grade(self, case: Case, response: str) -> Tuple[bool, float, str]: ...


# --------------------------------------------------------------------- #
class ExactMatchEvaluator:
    name = "exact_match"

    def __init__(self, *, case_sensitive: bool = False, strip: bool = True):
        self.case_sensitive = case_sensitive
        self.strip = strip

    def grade(self, case: Case, response: str) -> Tuple[bool, float, str]:
        if case.expected is None:
            return True, 1.0, "skip (no expected)"
        a, b = case.expected, response
        if self.strip:
            a, b = a.strip(), b.strip()
        if not self.case_sensitive:
            a, b = a.lower(), b.lower()
        ok = a == b
        return ok, (1.0 if ok else 0.0), "match" if ok else f"expected={case.expected!r}"


# --------------------------------------------------------------------- #
class RegexEvaluator:
    name = "regex"

    def grade(self, case: Case, response: str) -> Tuple[bool, float, str]:
        score = 1.0
        notes: List[str] = []
        if case.expected_regex:
            if not re.search(case.expected_regex, response, flags=re.MULTILINE | re.IGNORECASE):
                return False, 0.0, f"missing pattern {case.expected_regex!r}"
            notes.append("matched expected_regex")
        for forbidden in case.must_not_contain or []:
            if forbidden.lower() in response.lower():
                return False, 0.0, f"contains forbidden substring {forbidden!r}"
        if not notes:
            notes.append("no assertions")
        return True, score, "; ".join(notes)


# --------------------------------------------------------------------- #
def _bag_of_words_cosine(a: str, b: str) -> float:
    """Cheap fallback when sentence-transformers isn't installed. Bag-of-
    words cosine — bad for nuance, fine for "is the response on topic"."""
    import math
    from collections import Counter

    def vec(s: str) -> Counter:
        return Counter(re.findall(r"[A-Za-z']+", s.lower()))

    va, vb = vec(a), vec(b)
    common = set(va) & set(vb)
    dot = sum(va[w] * vb[w] for w in common)
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return dot / (na * nb) if na and nb else 0.0


class EmbeddingSimilarityEvaluator:
    name = "embedding_similarity"

    def __init__(
        self,
        *,
        threshold: float = 0.7,
        embed_fn: Optional[Callable[[List[str]], "np.ndarray"]] = None,  # noqa: F821
    ):
        self.threshold = threshold
        self._embed_fn = embed_fn
        self._loaded_st = False

    def _embed(self, texts: List[str]):
        if self._embed_fn is not None:
            return self._embed_fn(texts)
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            import numpy as np  # noqa: F401
            if not self._loaded_st:
                self._st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                self._loaded_st = True
            return self._st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        except ImportError:
            return None  # signal fallback

    def grade(self, case: Case, response: str) -> Tuple[bool, float, str]:
        if case.expected is None:
            return True, 1.0, "skip (no expected)"
        vecs = self._embed([case.expected, response])
        if vecs is None:
            score = _bag_of_words_cosine(case.expected, response)
            detail = f"BoW cosine={score:.3f} (sentence-transformers not installed)"
        else:
            import numpy as np
            score = float(np.dot(vecs[0], vecs[1]))
            detail = f"st cosine={score:.3f}"
        return score >= self.threshold, max(0.0, min(1.0, score)), detail


# --------------------------------------------------------------------- #
@dataclass
class _JudgeVerdict:
    score: float
    detail: str


class LLMJudgeEvaluator:
    name = "llm_judge"

    JUDGE_PROMPT = (
        "You are an impartial grader. Given a prompt, a reference answer, and a candidate response, "
        "rate the candidate from 1 to 5 on how well it answers the prompt compared to the reference. "
        "Reply with the integer score on the first line and a one-sentence justification on the second. "
        "Be strict: invented facts or off-topic responses score 1-2; concise correct answers score 5."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        threshold: float = 0.6,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("JUDGE_MODEL", "gpt-4o-mini")
        self._client = client
        self.threshold = threshold

    def _judge(self, prompt: str, reference: str, candidate: str) -> _JudgeVerdict:
        client = self._client or httpx.Client(timeout=60.0)
        user_msg = (
            f"PROMPT:\n{prompt}\n\n"
            f"REFERENCE ANSWER:\n{reference}\n\n"
            f"CANDIDATE RESPONSE:\n{candidate}\n"
        )
        r = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.JUDGE_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.0,
                "max_tokens": 120,
            },
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        first_line, *rest = content.split("\n", 1)
        m = re.search(r"\d+", first_line)
        raw = int(m.group(0)) if m else 1
        raw = max(1, min(5, raw))
        score = (raw - 1) / 4.0  # 1->0, 5->1
        justification = (rest[0].strip() if rest else "").splitlines()[0] if rest else ""
        return _JudgeVerdict(score=score, detail=f"judge={raw}/5: {justification}")

    def grade(self, case: Case, response: str) -> Tuple[bool, float, str]:
        if case.expected is None:
            return True, 1.0, "skip (no expected)"
        if not self.api_key:
            return False, 0.0, "OPENAI_API_KEY not set; judge disabled"
        verdict = self._judge(case.prompt, case.expected, response)
        return verdict.score >= self.threshold, verdict.score, verdict.detail
