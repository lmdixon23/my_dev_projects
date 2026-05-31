"""Synthesize tiny battery telemetry CSVs that match the project's column contract.

Real Li-ion accelerated-life data is GB-scale and not committable. This
generator produces ~200 rows per battery with the columns the rest of
the pipeline reads, so `python -m src.data_preprocessing` and the
downstream training/eval scripts run end-to-end.

Output layout matches what `config.yaml` expects:

    data/battery_alt_dataset/regular_alt_batteries/*.csv
    data/battery_alt_dataset/recommissioned_alt_batteries/*.csv
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

REGULAR_DIR = "data/battery_alt_dataset/regular_alt_batteries"
RECOMMISSIONED_DIR = "data/battery_alt_dataset/recommissioned_batteries"


def _synthesize_battery(n_rows: int, fail_early: bool, seed: int) -> pd.DataFrame:
    """One battery's worth of telemetry.

    `relative time` is in seconds (the real units). The downstream
    preprocessor divides by 3600 to convert to hours and labels rows
    where the hour reading exceeds the configured threshold as failures.
    """
    rng = np.random.default_rng(seed)
    # If `fail_early` is True, accumulate seconds quickly so many rows exceed
    # the 1000-hour failure threshold. Otherwise stay well below it.
    step_seconds = 30_000 if fail_early else 5_000
    rel_time_s = np.cumsum(rng.uniform(0.5 * step_seconds, 1.5 * step_seconds, size=n_rows))
    current = rng.normal(loc=1.2, scale=0.15, size=n_rows)
    voltage = rng.normal(loc=3.7, scale=0.05, size=n_rows)
    temperature = rng.normal(loc=27.0, scale=2.5, size=n_rows)
    capacity = np.clip(2.5 - rel_time_s / 1e7 + rng.normal(0, 0.05, n_rows), 0, None)

    return pd.DataFrame(
        {
            "relative time": rel_time_s,
            "current load": current,
            "voltage": voltage,
            "temperature": temperature,
            "capacity": capacity,
            "start time": "2025-01-01",  # ignored by preprocessor
            "mode": "constant" if not fail_early else "variable",  # ignored
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-folder", type=int, default=3,
                        help="how many battery CSVs to write per category")
    parser.add_argument("--rows", type=int, default=200,
                        help="rows per battery file")
    args = parser.parse_args()

    os.makedirs(REGULAR_DIR, exist_ok=True)
    os.makedirs(RECOMMISSIONED_DIR, exist_ok=True)

    for i in range(args.per_folder):
        _synthesize_battery(args.rows, fail_early=False, seed=100 + i).to_csv(
            os.path.join(REGULAR_DIR, f"battery_regular_{i:02d}.csv"), index=False
        )
        _synthesize_battery(args.rows, fail_early=True, seed=200 + i).to_csv(
            os.path.join(RECOMMISSIONED_DIR, f"battery_recom_{i:02d}.csv"), index=False
        )

    print(
        f"Wrote {args.per_folder} files each ({args.rows} rows) to "
        f"{REGULAR_DIR}/ and {RECOMMISSIONED_DIR}/."
    )


if __name__ == "__main__":
    main()
