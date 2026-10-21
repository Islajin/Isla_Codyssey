"""Behavior tests for persistence, CSV validation, sorting, and CLI errors."""

import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from budget_app.models import AppError
from budget_app.service import BudgetService
from budget_app.storage import LedgerStore, newest_first


class BudgetAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = BudgetService(LedgerStore(self.root / "data"))

    def add(self, date="2024-01-15", type="expense", category="food", amount="15000", memo="점심", tags="meal"):
        return self.service.add(date=date, type=type, category=category,
                                amount=amount, memo=memo, tags=tags)

    def test_crud_search_summary_budget_and_persistence(self) -> None:
        first = self.add(date="2024-01-01", amount="100")
        second = self.add(date="2024-01-20", category="transport", amount="200")
        income = self.add(date="2024-01-10", type="income", category="salary", amount="1000")
        self.assertEqual([item.id for item in self.service.list(2)], [second.id, income.id])
        self.assertEqual([item.id for item in self.service.search(category="food", tag="meal")], [first.id])
        self.service.set_budget("2024-01", "250")
        summary = BudgetService(LedgerStore(self.root / "data")).summary("2024-01", 2)
        self.assertEqual((summary.income, summary.expense, summary.balance, summary.budget),
                         (1000, 300, 700, 250))
        self.assertEqual(summary.top_categories, [("transport", 200), ("food", 100)])
        self.assertTrue(self.service.update(first.id, amount="150", memo="저녁"))
        self.assertEqual(next(self.service.search(q="저녁")).amount, 150)
        with self.assertRaises(AppError):
            self.service.remove_category("food")
        self.assertTrue(self.service.delete(first.id))
        self.assertFalse(self.service.delete("missing"))
        self.service.remove_category("food")
        self.assertNotIn("food", LedgerStore(self.root / "data").categories())

    def test_invalid_update_and_import_leave_data_intact(self) -> None:
        item = self.add()
        original = (self.root / "data" / "transactions.jsonl").read_bytes()
        with self.assertRaises(AppError):
            self.service.update(item.id, amount="0")
        self.assertEqual((self.root / "data" / "transactions.jsonl").read_bytes(), original)
        source = self.root / "bad.csv"
        source.write_text("date,type,category,amount,memo,tags\n"
                          "2024-01-01,expense,food,10,ok,\n"
                          "2024-02-30,expense,food,20,bad,\n", encoding="utf-8")
        with self.assertRaises(AppError):
            self.service.import_csv(source)
        self.assertEqual((self.root / "data" / "transactions.jsonl").read_bytes(), original)

    def test_csv_round_trip_and_cli_error_code(self) -> None:
        self.add(memo="점심, 간식", tags="meal,friend")
        out = self.root / "out.csv"
        self.assertEqual(self.service.export_csv(out, month="2024-01"), 1)
        with out.open(encoding="utf-8", newline="") as file:
            row = next(csv.DictReader(file))
        self.assertEqual(row["memo"], "점심, 간식")
        self.assertEqual(row["tags"], "meal,friend")
        second = BudgetService(LedgerStore(self.root / "second"))
        self.assertEqual(second.import_csv(out), 1)
        self.assertEqual(next(second.list(1)).memo, "점심, 간식")
        run = subprocess.run(
            [sys.executable, "-m", "budget_app", "--data-dir", str(self.root / "data"),
             "delete", "--id", "missing"], capture_output=True, text=True,
        )
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("거래가 없습니다", run.stderr)
        self.assertNotIn("Traceback", run.stderr)

    def test_external_sort_across_chunks(self) -> None:
        dates = ("2024-01-02", "2024-01-05", "2024-01-01", "2024-01-04", "2024-01-03")
        for day in dates:
            self.add(date=day)
        sorted_items = newest_first(self.service.store.transactions(), chunk_size=2)
        self.assertEqual([item.date for item in sorted_items], sorted(dates, reverse=True))


if __name__ == "__main__":
    unittest.main()
