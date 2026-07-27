"""Validation and deterministic regression tests for the checked-in benchmark."""

import json
import unittest
from collections import Counter
from pathlib import Path

from rag.chunker import Chunker, Document
from rag.embedder import HashEmbedder
from rag.eval import (
    REQUIRED_BENCHMARK_TAGS,
    eval_retrieval,
    load_eval_cases,
    validate_eval_cases,
)
from rag.retriever import Retriever
from rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "sample_docs"
BASELINE_PATH = SAMPLE_DIR / "hash_baseline_v1.json"


def load_documents():
    return [
        Document(source=path.name, text=path.read_text(encoding="utf-8"))
        for path in sorted(SAMPLE_DIR.glob("*.md"))
    ]


def run_hash_baseline():
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    documents = load_documents()
    cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
    embedder = HashEmbedder(dim=baseline["embedder"]["dim"])
    chunker = Chunker(**baseline["chunker"])
    chunks = chunker.chunk_corpus(documents)
    store = VectorStore(dim=embedder.dim)
    store.add(chunks, embedder.embed([chunk.text for chunk in chunks]))
    return baseline, documents, chunks, cases, eval_retrieval(
        Retriever(embedder, store), cases, k=3
    )


class TestBenchmarkDataset(unittest.TestCase):
    def test_benchmark_has_40_cases_and_10_documents(self):
        cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
        documents = load_documents()

        self.assertEqual(len(cases), 40)
        self.assertEqual(len(documents), 10)

    def test_dataset_passes_schema_and_source_validation(self):
        cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
        documents = load_documents()

        validate_eval_cases(cases, [document.source for document in documents])

    def test_each_required_category_has_eight_cases(self):
        cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
        counts = Counter(tag for case in cases for tag in case.tags)

        for tag in REQUIRED_BENCHMARK_TAGS:
            self.assertEqual(counts[tag], 8, tag)

    def test_dataset_contains_multi_source_labels(self):
        cases = load_eval_cases(SAMPLE_DIR / "eval_cases.json")
        multi_source = [case for case in cases if len(case.relevant_sources) > 1]

        self.assertGreaterEqual(len(multi_source), 3)

    def test_baseline_metadata_matches_corpus_and_chunking(self):
        baseline, documents, chunks, cases, _ = run_hash_baseline()

        self.assertEqual(baseline["benchmark_version"], "rag-retrieval-v1")
        self.assertEqual(baseline["corpus"]["documents"], len(documents))
        self.assertEqual(baseline["corpus"]["chunks"], len(chunks))
        self.assertEqual(baseline["corpus"]["sources"], [doc.source for doc in documents])
        self.assertEqual(baseline["cases"], len(cases))

    def test_hash_baseline_stays_above_regression_thresholds(self):
        baseline, _, _, _, result = run_hash_baseline()
        thresholds = baseline["regression_thresholds"]

        self.assertGreaterEqual(result.recall_at_1, thresholds["min_recall_at_1"])
        self.assertGreaterEqual(result.recall_at_3, thresholds["min_recall_at_3"])
        self.assertGreaterEqual(result.mrr, thresholds["min_mrr"])

        for tag, minimum in thresholds["min_required_tag_recall_at_3"].items():
            self.assertGreaterEqual(result.by_tag[tag]["recall_at_3"], minimum, tag)


if __name__ == "__main__":
    unittest.main()
