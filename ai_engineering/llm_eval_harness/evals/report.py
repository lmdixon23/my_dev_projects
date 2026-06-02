"""Render an `EvalRun` to a standalone HTML page.

The output is intentionally a single self-contained file — no external
CSS, no JS framework, no images — so it can be uploaded as a CI
artifact and viewed without infrastructure. The styling is a small
inline `<style>` block.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone

from .cases import EvalRun


_CSS = """
body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       margin: 2em; max-width: 1100px; color: #222; }
h1 { margin-bottom: 0.2em; }
.summary { background: #f5f7fa; padding: 1em; border-radius: 6px; margin: 1em 0; }
.summary .big { font-size: 24px; font-weight: 600; }
table { width: 100%; border-collapse: collapse; margin: 1em 0; }
th, td { border-bottom: 1px solid #eee; padding: 8px 6px; text-align: left;
         vertical-align: top; font-size: 13px; }
th { background: #fafafa; }
.pass { color: #1a7f37; font-weight: 600; }
.fail { color: #c92a2a; font-weight: 600; }
.prompt, .response { white-space: pre-wrap; max-width: 320px; font-family: ui-monospace, monospace; }
.detail { color: #555; font-style: italic; }
.group-header { background: #eef; }
"""


class HTMLReport:
    @staticmethod
    def render(run: EvalRun) -> str:
        rows = []
        for ev_name, results in run.grouped_by_evaluator().items():
            rows.append(
                f"<tr class='group-header'><th colspan='6'>Evaluator: <code>{html.escape(ev_name)}</code></th></tr>"
            )
            for r in results:
                cls = "pass" if r.passed else "fail"
                tag = "PASS" if r.passed else "FAIL"
                rows.append(
                    "<tr>"
                    f"<td>{html.escape(r.case_id)}</td>"
                    f"<td class='prompt'>{html.escape(r.prompt[:400])}</td>"
                    f"<td class='response'>{html.escape(r.response[:400])}</td>"
                    f"<td class='{cls}'>{tag}</td>"
                    f"<td>{r.score:.2f}</td>"
                    f"<td class='detail'>{html.escape(r.detail)}</td>"
                    "</tr>"
                )

        return (
            f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(run.suite_name)} — LLM Eval Report</title>"
            f"<style>{_CSS}</style></head><body>"
            f"<h1>{html.escape(run.suite_name)}</h1>"
            f"<div class='summary'>"
            f"<div class='big'>{run.passed()}/{run.total()} passed "
            f"({run.pass_rate() * 100:.1f}%)</div>"
            f"<div>Generated {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z</div>"
            f"</div>"
            f"<table>"
            f"<thead><tr><th>Case</th><th>Prompt</th><th>Response</th>"
            f"<th>Verdict</th><th>Score</th><th>Detail</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            f"</table>"
            f"</body></html>"
        )

    @staticmethod
    def write(run: EvalRun, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(HTMLReport.render(run))
