"""Generate the `sales_data.csv` file that the SSIS package consumes.

The original version produced 5 always-clean rows. This expanded version:
  * Generates `--rows N` clean rows of realistic-ish sales activity.
  * Inserts a small number of intentionally bad rows (bad date, negative
    quantity, unparseable price) so the SSIS package's error-redirect
    branch and the Python reference ETL's validation path both have
    something real to reject.

Usage:
    python create_sales_data.py                 # 100 clean + ~3 bad rows
    python create_sales_data.py --rows 1000     # bigger dataset
    python create_sales_data.py --clean-only    # no bad rows
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta

PRODUCTS = [
    (101, "Laptop", 1000.0),
    (102, "Smartphone", 800.0),
    (103, "Headphones", 200.0),
    (104, "Monitor", 350.0),
    (105, "Keyboard", 75.0),
    (106, "Mouse", 45.0),
    (107, "Tablet", 600.0),
    (108, "Smartwatch", 250.0),
]

HEADER = [
    "OrderID", "OrderDate", "CustomerID", "ProductID",
    "ProductName", "Quantity", "UnitPrice", "TotalPrice",
]


def _clean_row(order_id: int, seed: random.Random) -> list[str]:
    pid, pname, price = seed.choice(PRODUCTS)
    qty = seed.randint(1, 5)
    d = date(2024, 1, 1) + timedelta(days=seed.randint(0, 365))
    return [
        str(order_id),
        d.isoformat(),
        str(500 + seed.randint(0, 4999)),
        str(pid),
        pname,
        str(qty),
        f"{price:.2f}",
        f"{price * qty:.2f}",
    ]


def _bad_rows(order_ids: list[int]) -> list[list[str]]:
    """Three rows that should be rejected by a strict ETL."""
    return [
        [str(order_ids[0]), "NOT-A-DATE", "501", "101", "Laptop", "1", "1000.00", "1000.00"],
        [str(order_ids[1]), "2024-04-15", "502", "102", "Smartphone", "-1", "800.00", "800.00"],
        [str(order_ids[2]), "2024-04-16", "503", "103", "Headphones", "1", "two_hundred", "200.00"],
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="sales_data.csv")
    parser.add_argument("--clean-only", action="store_true")
    args = parser.parse_args()

    seed = random.Random(args.seed)
    clean = [_clean_row(1000 + i, seed) for i in range(args.rows)]
    bad = [] if args.clean_only else _bad_rows(
        [2000 + args.rows, 2001 + args.rows, 2002 + args.rows]
    )
    all_rows = clean + bad

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        writer.writerows(all_rows)
    print(f"Wrote {len(clean)} clean + {len(bad)} intentionally bad rows to {args.out}.")


if __name__ == "__main__":
    main()
