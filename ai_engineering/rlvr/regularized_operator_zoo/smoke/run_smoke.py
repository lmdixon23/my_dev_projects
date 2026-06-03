"""End-to-end smoke run.

Sweeps beta from 0.01 to 100 for each operator on a fixed q = [1, 2, 0.5]
and writes:

  reports/policy_vs_beta.png      -- one line per operator, three subplots
  reports/smoke_report.md         -- summary + identity check per operator
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np

from operator_zoo import RegularizedOp


REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)


def main() -> None:
    q = np.array([1.0, 2.0, 0.5])
    n_actions = q.size
    betas = np.geomspace(0.01, 100.0, num=40)

    operators = [
        ("entropy",     {}),
        ("kl_uniform",  {}),
        ("kl_anchor",   {"anchor": np.array([0.6, 0.3, 0.1])}),
        ("tsallis",     {}),
    ]

    # ----- Plot ----- #
    fig, axes = plt.subplots(1, n_actions, figsize=(13, 4), sharey=True)
    for ax_idx in range(n_actions):
        ax = axes[ax_idx]
        for name, kwargs in operators:
            ys = []
            for b in betas:
                pi = RegularizedOp(name, beta=float(b), **kwargs).policy(q)
                ys.append(pi[ax_idx])
            ax.plot(betas, ys, label=name)
        ax.set_xscale("log")
        ax.set_xlabel("beta")
        ax.set_title(f"pi(action {ax_idx}) | q = {q.tolist()}")
        if ax_idx == 0:
            ax.set_ylabel("probability")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    plt.tight_layout()
    plot_path = REPORTS / "policy_vs_beta.png"
    plt.savefig(plot_path, dpi=120)
    plt.close(fig)

    # ----- Numeric identity check ----- #
    def finite_diff_gradient(op, q, eps=1e-6):
        g = np.zeros_like(q)
        for i in range(q.size):
            qp = q.copy(); qp[i] += eps
            qm = q.copy(); qm[i] -= eps
            g[i] = (op.value(qp) - op.value(qm)) / (2 * eps)
        return g

    lines = [
        f"# Regularized Operator Zoo — Smoke Run",
        f"",
        f"_Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')}Z_",
        f"",
        f"q = {q.tolist()}, beta = 1.0",
        f"",
        f"## Identity 1 — gradient form: pi* = grad Omega*(q)",
        f"",
        f"Verified by central finite difference of Omega*. The closed-form",
        f"operators should agree to ~1e-6; chi2 is solver-based and uses a",
        f"looser tolerance.",
        f"",
        f"| Operator | ||pi - grad Omega*||_2 |",
        f"|---|---|",
    ]
    for name, kwargs in operators + [("chi2", {})]:
        op = RegularizedOp(name, beta=1.0, **kwargs)
        pi = op.policy(q)
        grad_star = finite_diff_gradient(op, q)
        lines.append(f"| {name} | {float(np.linalg.norm(pi - grad_star)):.2e} |")

    lines += [
        f"",
        f"## Identity 2 — conjugate form: Omega*(q) == <pi, q> - Omega(pi)",
        f"",
        f"| Operator | Omega*(q) | <pi, q> - Omega(pi) | diff |",
        f"|---|---|---|---|",
    ]
    for name, kwargs in operators + [("chi2", {})]:
        op = RegularizedOp(name, beta=1.0, **kwargs)
        pi = op.policy(q)
        lhs = op.value(q)
        rhs = float(np.dot(pi, q) - op.omega(pi))
        lines.append(f"| {name} | {lhs:.6f} | {rhs:.6f} | {abs(lhs - rhs):.2e} |")

    lines += [
        "",
        f"## Sweep plot",
        "",
        f"![policy vs beta](./policy_vs_beta.png)",
        "",
        f"Each subplot shows pi(action i) as beta sweeps from 0.01 to 100",
        f"under four different regularizers. Small beta -> nearly greedy on",
        f"argmax(q); large beta -> nearly the anchor (uniform or the configured mu).",
    ]

    (REPORTS / "smoke_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {plot_path} and {REPORTS / 'smoke_report.md'}")


if __name__ == "__main__":
    main()
