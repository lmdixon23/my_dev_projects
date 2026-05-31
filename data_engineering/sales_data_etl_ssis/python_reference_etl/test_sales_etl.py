"""Unit tests for the Python reference ETL's transform/validation logic."""

import os
import sqlite3
import tempfile
import unittest

from sales_etl import run_sqlite, transform_row


class TestTransform(unittest.TestCase):
    def test_clean_row_passes(self):
        row = transform_row({
            "OrderID": "1001", "OrderDate": "2024-01-15", "CustomerID": "501",
            "ProductID": "101", "ProductName": "Laptop", "Quantity": "1",
            "UnitPrice": "1000.00", "TotalPrice": "1000.00",
        })
        self.assertEqual(row.OrderID, 1001)
        self.assertEqual(row.OrderDate.year, 2024)

    def test_bad_date_rejected(self):
        with self.assertRaises(ValueError):
            transform_row({
                "OrderID": "1", "OrderDate": "garbage", "CustomerID": "1",
                "ProductID": "1", "ProductName": "X", "Quantity": "1",
                "UnitPrice": "1.0", "TotalPrice": "1.0",
            })

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            transform_row({
                "OrderID": "1", "OrderDate": "2024-01-01", "CustomerID": "1",
                "ProductID": "1", "ProductName": "X", "Quantity": "-1",
                "UnitPrice": "1.0", "TotalPrice": "1.0",
            })


class TestSQLiteLoader(unittest.TestCase):
    def test_full_run_into_sqlite_writes_clean_and_rejects_bad(self):
        tmp = tempfile.mkdtemp()
        csv_path = os.path.join(tmp, "in.csv")
        db_path = os.path.join(tmp, "out.sqlite")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write(
                "OrderID,OrderDate,CustomerID,ProductID,ProductName,Quantity,UnitPrice,TotalPrice\n"
                "1,2024-01-01,1,1,Laptop,1,1000.0,1000.0\n"
                "2,2024-01-02,2,2,Phone,2,500.0,1000.0\n"
                "3,not-a-date,3,3,X,1,1.0,1.0\n"
            )
        read, written, rejected = run_sqlite(csv_path, db_path)
        self.assertEqual((read, written, rejected), (3, 2, 1))
        con = sqlite3.connect(db_path)
        self.assertEqual(
            con.execute("SELECT COUNT(*) FROM SalesData").fetchone()[0], 2
        )
        self.assertEqual(
            con.execute("SELECT COUNT(*) FROM SalesData_ErrorLog").fetchone()[0], 1
        )


if __name__ == "__main__":
    unittest.main()
