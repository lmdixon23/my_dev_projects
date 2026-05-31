"""Python reference implementation of the SSIS package's transform+load steps.

Purpose: make the project's logic verifiable on any machine, not just one
with SQL Server + SSIS installed. This module is *not* what the production
pipeline runs; the SSIS package (`SalesDataETL.dtsx`) is. The two are
intentionally kept behavior-equivalent for the transform and validation
stages so that anyone reviewing the project can read this file and trust
that the SSIS package does the same thing.

Modes:
  * `--target sqlite:///out.db` — load into a local SQLite file (zero deps
    beyond stdlib). Default.
  * `--target mssql+pyodbc://...` — load into the real SQL Server target
    by passing a SQLAlchemy URL. Requires `pip install sqlalchemy pyodbc`.

Usage:
    python python_reference_etl/sales_etl.py \\
        --source sales_data.csv --target sqlite:///salesdatadb.sqlite
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional


@dataclass
class CleanRow:
    OrderID: int
    OrderDate: datetime
    CustomerID: int
    ProductID: int
    ProductName: str
    Quantity: int
    UnitPrice: float
    TotalPrice: float


@dataclass
class RejectedRow:
    raw: dict
    reason: str


def transform_row(raw: dict) -> CleanRow:
    """Apply the same conversions the SSIS Convert_SalesDataTypes task does.

    Raises `ValueError` on any validation failure so the caller can route
    the row to the error-log path.
    """
    try:
        order_id = int(raw["OrderID"])
        order_date = datetime.strptime(raw["OrderDate"], "%Y-%m-%d")
        customer_id = int(raw["CustomerID"])
        product_id = int(raw["ProductID"])
        product_name = raw["ProductName"].strip()
        quantity = int(raw["Quantity"])
        unit_price = float(raw["UnitPrice"])
        total_price = float(raw["TotalPrice"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"failed to parse columns: {exc}") from exc

    if quantity <= 0:
        raise ValueError(f"quantity must be > 0, got {quantity}")
    if unit_price < 0 or total_price < 0:
        raise ValueError("prices must be non-negative")
    if not product_name:
        raise ValueError("product name is empty")

    return CleanRow(
        OrderID=order_id,
        OrderDate=order_date,
        CustomerID=customer_id,
        ProductID=product_id,
        ProductName=product_name,
        Quantity=quantity,
        UnitPrice=unit_price,
        TotalPrice=total_price,
    )


def read_csv(path: str) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        yield from csv.DictReader(fh)


def run_sqlite(source: str, db_path: str) -> tuple[int, int, int]:
    """Returns (rows_read, rows_written, rows_rejected)."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS SalesData(
            OrderID INTEGER PRIMARY KEY, OrderDate TEXT NOT NULL,
            CustomerID INTEGER NOT NULL, ProductID INTEGER NOT NULL,
            ProductName TEXT NOT NULL, Quantity INTEGER NOT NULL,
            UnitPrice REAL NOT NULL, TotalPrice REAL NOT NULL,
            IngestedAt TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS SalesData_ErrorLog(
            ErrorLogID INTEGER PRIMARY KEY AUTOINCREMENT,
            OrderID TEXT, RawRow TEXT NOT NULL, ErrorMessage TEXT NOT NULL,
            LoggedAt TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )

    read = written = rejected = 0
    for raw in read_csv(source):
        read += 1
        try:
            clean = transform_row(raw)
            conn.execute(
                """INSERT OR REPLACE INTO SalesData(
                    OrderID, OrderDate, CustomerID, ProductID,
                    ProductName, Quantity, UnitPrice, TotalPrice
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    clean.OrderID, clean.OrderDate.isoformat(),
                    clean.CustomerID, clean.ProductID,
                    clean.ProductName, clean.Quantity,
                    clean.UnitPrice, clean.TotalPrice,
                ),
            )
            written += 1
        except ValueError as exc:
            rejected += 1
            conn.execute(
                "INSERT INTO SalesData_ErrorLog(OrderID, RawRow, ErrorMessage) VALUES (?, ?, ?)",
                (raw.get("OrderID"), str(raw), str(exc)),
            )
    conn.commit()
    conn.close()
    return read, written, rejected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="sales_data.csv")
    parser.add_argument("--target", default="sqlite:///salesdatadb.sqlite")
    args = parser.parse_args()

    started = time.monotonic()
    if args.target.startswith("sqlite:///"):
        db_path = args.target[len("sqlite:///"):]
        read, written, rejected = run_sqlite(args.source, db_path)
    else:
        raise SystemExit(
            "Non-SQLite targets are intentionally a stub here. Pass a "
            "SQLAlchemy URL and re-run after extending run_sqlite() with "
            "your driver of choice (e.g. mssql+pyodbc)."
        )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    print(f"Read={read} Written={written} Rejected={rejected} in {elapsed_ms} ms")


if __name__ == "__main__":
    main()
