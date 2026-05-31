"""End-to-end smoke run for the battery predictive-maintenance pipeline.

Steps:
    1. Synthesize tiny battery CSVs.
    2. Preprocess -> split + scaler.
    3. Train Random Forest.
    4. Evaluate, write reports/smoke_eval.md.
"""

from __future__ import annotations

import os
from datetime import datetime

from smoke.generate_dataset import main as generate_dataset_main
from src.data_preprocessing import main as preprocess_main
from src.evaluation import evaluate
from src.model_training import train

REPORT_PATH = "reports/smoke_eval.md"


def main() -> None:
    # 1. Data
    generate_dataset_main_args = ["--per-folder", "3", "--rows", "200"]
    # generate_dataset_main reads sys.argv via argparse; easiest is to just call
    # the underlying helper directly.
    from smoke.generate_dataset import _synthesize_battery, REGULAR_DIR, RECOMMISSIONED_DIR
    os.makedirs(REGULAR_DIR, exist_ok=True)
    os.makedirs(RECOMMISSIONED_DIR, exist_ok=True)
    for i in range(3):
        _synthesize_battery(200, fail_early=False, seed=100 + i).to_csv(
            os.path.join(REGULAR_DIR, f"battery_regular_{i:02d}.csv"), index=False
        )
        _synthesize_battery(200, fail_early=True, seed=200 + i).to_csv(
            os.path.join(RECOMMISSIONED_DIR, f"battery_recom_{i:02d}.csv"), index=False
        )

    # 2-3. Preprocess + train
    preprocess_main()
    train()

    # 4. Evaluate (also writes reports/evaluation_report.txt)
    metrics = evaluate()

    os.makedirs(os.path.dirname(REPORT_PATH) or ".", exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(
            "# Predictive Maintenance — Smoke Run\n\n"
            f"_Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z_\n\n"
            "Synthesized 3 'regular' + 3 'recommissioned' battery CSVs (200 rows "
            "each) and ran the full preprocessing + training + evaluation "
            "pipeline. Real Li-ion telemetry is GB-scale and not committed; "
            "see README1.md for how to point this at a real dataset.\n\n"
            f"## Headline metrics\n\n"
            f"- **Accuracy:** {metrics['accuracy']:.4f}\n"
            f"- **Weighted F1:** {metrics['f1']:.4f}\n\n"
            "See `reports/evaluation_report.txt` for the full classification "
            "report and confusion matrix.\n"
        )
    print(f"Wrote smoke report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
