"""End-to-end runner + report tests using a deterministic respond_fn."""

import os
import tempfile
import unittest

from evals.cases import Case, EvalRun
from evals.evaluators import ExactMatchEvaluator, RegexEvaluator
from evals.report import HTMLReport
from evals.runner import Runner


class TestRunner(unittest.TestCase):
    def test_runs_all_evaluators_against_all_cases(self):
        cases = [
            Case(id="c1", prompt="capital of France?", expected="Paris"),
            Case(id="c2", prompt="say 'hello'", expected_regex=r"hello", must_not_contain=["world"]),
        ]
        responses = {"capital of France?": "Paris", "say 'hello'": "hello!"}
        runner = Runner(
            respond_fn=lambda p: responses[p],
            evaluators=[ExactMatchEvaluator(), RegexEvaluator()],
        )
        run = runner.run("demo", cases)
        # 2 cases x 2 evaluators = 4 results.
        self.assertEqual(run.total(), 4)
        self.assertEqual(run.passed(), 4)
        self.assertEqual(run.pass_rate(), 1.0)

    def test_failures_lower_pass_rate(self):
        cases = [
            Case(id="c1", prompt="?", expected="Paris"),
            Case(id="c2", prompt="?", expected="Berlin"),
        ]
        runner = Runner(
            respond_fn=lambda _p: "Paris",
            evaluators=[ExactMatchEvaluator()],
        )
        run = runner.run("demo", cases)
        self.assertEqual(run.passed(), 1)
        self.assertEqual(run.total(), 2)
        self.assertAlmostEqual(run.pass_rate(), 0.5)


class TestHTMLReport(unittest.TestCase):
    def test_html_contains_summary_and_rows(self):
        cases = [Case(id="c1", prompt="?", expected="x")]
        runner = Runner(
            respond_fn=lambda _p: "x",
            evaluators=[ExactMatchEvaluator()],
        )
        run = runner.run("html_test", cases)
        html = HTMLReport.render(run)
        self.assertIn("html_test", html)
        self.assertIn("PASS", html)

    def test_write_creates_file(self):
        cases = [Case(id="c1", prompt="?", expected="x")]
        run = Runner(
            respond_fn=lambda _p: "x",
            evaluators=[ExactMatchEvaluator()],
        ).run("disk_test", cases)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.html")
            HTMLReport.write(run, path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100)


if __name__ == "__main__":
    unittest.main()
