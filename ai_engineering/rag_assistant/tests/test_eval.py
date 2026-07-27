"""Unit tests for retrieval metrics, labels, loading, and category slices."""

import json
import tempfile
import unittest
from pathlib import Path

from rag.chunker import Chunk
from rag.eval import (
    EvalCase,
    REQUIRED_BENCHMARK_TAGS,
    eval_retrieval,
    load_eval_cases,
    validate_eval_cases,
)
from rag.retriever import RetrievedChunk


def retrieved(source: str, score: float = 1.0) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=f"{source}#0",
        doc_id=source,
        source=source,
        chunk_index=0,
        text=source,
    )
    return RetrievedChunk(score=score, chunk=chunk)


class FakeRetriever:
    def __init__(self, results_by_question):
        self.results_by_question = results_by_question
        self.requested_depths = []

    def retrieve(self, question: str, k: int = 5):
        self.requested_depths.append(k)
        return list(self.results_by_question.get(question, []))[:k]


class TestRetrievalMetrics(unittest.TestCase):
    def test_aggregate_recall_at_1_recall_at_3_recall_at_k_and_mrr(self):
        cases = [
            EvalCase("rank one", ["a.md"], id="a", tags=["direct_lookup"]),
            EvalCase("rank three", ["b.md"], id="b", tags=["paraphrase"]),
            EvalCase("missing", ["c.md"], id="c", tags=["hard_negative"]),
        ]
        fake = FakeRetriever(
            {
                "rank one": [retrieved("a.md"), retrieved("x.md"), retrieved("y.md")],
                "rank three": [retrieved("x.md"), retrieved("y.md"), retrieved("b.md")],
                "missing": [retrieved("x.md"), retrieved("y.md"), retrieved("z.md")],
            }
        )

        result = eval_retrieval(fake, cases, k=5)

        self.assertAlmostEqual(result.recall_at_1, 1 / 3)
        self.assertAlmostEqual(result.recall_at_3, 2 / 3)
        self.assertAlmostEqual(result.recall_at_k, 2 / 3)
        self.assertAlmostEqual(result.mrr, (1.0 + 1 / 3) / 3)
        self.assertEqual(result.k, 5)

    def test_multi_source_labels_accept_any_labeled_source(self):
        case = EvalCase(
            "shared answer",
            ["primary.md", "alternate.md"],
            id="multi",
            tags=["direct_lookup"],
        )
        fake = FakeRetriever(
            {"shared answer": [retrieved("alternate.md#section"), retrieved("noise.md")]}
        )

        result = eval_retrieval(fake, [case], k=3)

        self.assertEqual(result.recall_at_1, 1.0)
        self.assertEqual(result.per_case[0]["first_relevant_rank"], 1)
        self.assertEqual(result.per_case[0]["hit_ranks"], [1])

    def test_missing_hit_records_zero_metrics_and_no_rank(self):
        case = EvalCase("none", ["missing.md"], id="none", tags=["hard_negative"])
        fake = FakeRetriever({"none": [retrieved("noise.md")]})

        result = eval_retrieval(fake, [case], k=3)
        row = result.per_case[0]

        self.assertEqual(row["recall_at_1"], 0.0)
        self.assertEqual(row["recall_at_3"], 0.0)
        self.assertEqual(row["reciprocal_rank"], 0.0)
        self.assertIsNone(row["first_relevant_rank"])
        self.assertEqual(row["hit_ranks"], [])

    def test_tag_slices_aggregate_only_matching_cases(self):
        cases = [
            EvalCase("a", ["a.md"], id="a", tags=["direct_lookup", "rag"]),
            EvalCase("b", ["b.md"], id="b", tags=["paraphrase", "rag"]),
            EvalCase("c", ["c.md"], id="c", tags=["paraphrase", "vector"]),
        ]
        fake = FakeRetriever(
            {
                "a": [retrieved("a.md")],
                "b": [retrieved("x.md"), retrieved("b.md")],
                "c": [retrieved("x.md")],
            }
        )

        result = eval_retrieval(fake, cases, k=3)

        self.assertEqual(result.by_tag["rag"]["n_cases"], 2)
        self.assertEqual(result.by_tag["rag"]["recall_at_3"], 1.0)
        self.assertEqual(result.by_tag["paraphrase"]["n_cases"], 2)
        self.assertEqual(result.by_tag["paraphrase"]["recall_at_3"], 0.5)
        self.assertEqual(result.by_tag["vector"]["mrr"], 0.0)

    def test_k_one_still_retrieves_three_for_fixed_recall_at_3(self):
        case = EvalCase("q", ["target.md"], id="q", tags=["direct_lookup"])
        fake = FakeRetriever(
            {"q": [retrieved("noise.md"), retrieved("target.md"), retrieved("other.md")]}
        )

        result = eval_retrieval(fake, [case], k=1)

        self.assertEqual(fake.requested_depths, [3])
        self.assertEqual(result.recall_at_k, 0.0)
        self.assertEqual(result.recall_at_3, 1.0)

    def test_empty_cases_return_zero_metrics(self):
        result = eval_retrieval(FakeRetriever({}), [], k=3)

        self.assertEqual(result.n_cases, 0)
        self.assertEqual(result.recall_at_1, 0.0)
        self.assertEqual(result.recall_at_3, 0.0)
        self.assertEqual(result.mrr, 0.0)
        self.assertEqual(result.per_case, [])
        self.assertEqual(result.by_tag, {})

    def test_loader_preserves_legacy_and_enriched_cases(self):
        payload = [
            {"question": "legacy", "relevant_sources": ["a.md"]},
            {
                "id": "new-1",
                "question": "enriched",
                "relevant_sources": ["b.md"],
                "tags": ["direct_lookup"],
            },
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            cases = load_eval_cases(path)

        self.assertEqual(cases[0].question, "legacy")
        self.assertEqual(cases[0].id, "")
        self.assertEqual(cases[0].tags, [])
        self.assertEqual(cases[1].id, "new-1")
        self.assertEqual(cases[1].tags, ["direct_lookup"])

    def test_validation_rejects_duplicate_ids(self):
        cases = [
            EvalCase("a", ["a.md"], id="same", tags=list(REQUIRED_BENCHMARK_TAGS)),
            EvalCase("b", ["a.md"], id="same", tags=["direct_lookup"]),
        ]
        with self.assertRaisesRegex(ValueError, "duplicate case id"):
            validate_eval_cases(cases, ["a.md"])

    def test_validation_rejects_missing_sources_and_required_tags(self):
        missing_source = [
            EvalCase(
                "a",
                ["missing.md"],
                id="a",
                tags=list(REQUIRED_BENCHMARK_TAGS),
            )
        ]
        with self.assertRaisesRegex(ValueError, "missing sources"):
            validate_eval_cases(missing_source, ["a.md"])

        missing_tags = [
            EvalCase("a", ["a.md"], id="a", tags=["direct_lookup"])
        ]
        with self.assertRaisesRegex(ValueError, "missing required tags"):
            validate_eval_cases(missing_tags, ["a.md"])


if __name__ == "__main__":
    unittest.main()
