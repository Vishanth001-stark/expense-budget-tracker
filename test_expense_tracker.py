"""
test_expense_tracker.py
Comprehensive automated test suite for Personal Expense & Budget Tracker.
Covers Models, Validators, Storage CSV parsing, Analytics, and Tracker CRUD.
"""

import os
import shutil
import tempfile
import unittest
from models import Expense, MonthlyBudget
from validators import (
    validate_date,
    validate_month,
    validate_amount,
    validate_category,
    validate_payment_method,
    validate_description
)
from storage import StorageManager
from tracker import ExpenseTracker
import analytics


class TestValidators(unittest.TestCase):

    def test_validate_date_formats(self):
        ok, parsed, _ = validate_date("2026-09-27")
        self.assertTrue(ok)
        self.assertEqual(parsed, "2026-09-27")

        ok, parsed, _ = validate_date("today")
        self.assertTrue(ok)
        self.assertIsNotNone(parsed)

        ok, _, err = validate_date("27-09-2026")
        self.assertFalse(ok)
        self.assertIn("Invalid date format", err)

    def test_validate_amount(self):
        ok, amt, _ = validate_amount("250.50")
        self.assertTrue(ok)
        self.assertEqual(amt, 250.50)

        ok, _, err = validate_amount("-50")
        self.assertFalse(ok)
        self.assertIn("strictly greater than 0", err)

        ok, _, err = validate_amount("abc")
        self.assertFalse(ok)
        self.assertIn("valid numeric number", err)

    def test_validate_category(self):
        ok, cat, _ = validate_category("Food & Dining")
        self.assertTrue(ok)
        self.assertEqual(cat, "Food & Dining")

        ok, cat, _ = validate_category("1")
        self.assertTrue(ok)
        self.assertEqual(cat, "Food & Dining")

        ok, _, err = validate_category("InvalidCategory")
        self.assertFalse(ok)
        self.assertIn("Invalid category", err)

    def test_validate_payment_method(self):
        ok, method, _ = validate_payment_method("UPI")
        self.assertTrue(ok)
        self.assertEqual(method, "UPI")

        ok, method, _ = validate_payment_method("1")
        self.assertTrue(ok)
        self.assertEqual(method, "UPI")

        ok, _, err = validate_payment_method("Bitcoin")
        self.assertFalse(ok)
        self.assertIn("Invalid payment method", err)


class TestStorageAndPersistence(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_expense_storage_")
        self.storage = StorageManager(data_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_expenses(self):
        expenses = [
            Expense("EXP-01", "2026-09-01", 100.0, "Food & Dining", "Coffee", "UPI"),
            Expense("EXP-02", "2026-09-02", 500.0, "Transportation", "Metro", "Cash")
        ]
        self.storage.save_expenses(expenses)

        loaded, corrupt = self.storage.load_expenses()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(corrupt, 0)
        self.assertEqual(loaded[0].id, "EXP-01")
        self.assertEqual(loaded[1].amount, 500.0)

    def test_corrupt_csv_line_handling(self):
        # Write CSV with one good row and one corrupt row
        with open(self.storage.expenses_file, "w", encoding="utf-8") as f:
            f.write("id,date,amount,category,description,payment_method,created_at\n")
            f.write("EXP-01,2026-09-01,150.00,Food & Dining,Lunch,UPI,2026-09-01\n")
            f.write("CORRUPT,INVALID_DATE,-99,Unknown,Corrupt,None,\n")

        loaded, corrupt = self.storage.load_expenses()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(corrupt, 1)
        self.assertEqual(loaded[0].id, "EXP-01")


class TestAnalytics(unittest.TestCase):

    def test_category_aggregation(self):
        expenses = [
            Expense("1", "2026-09-01", 200.0, "Food & Dining", "Lunch"),
            Expense("2", "2026-09-02", 300.0, "Food & Dining", "Dinner"),
            Expense("3", "2026-09-03", 500.0, "Education & Books", "Book")
        ]
        cat_data = analytics.aggregate_by_category(expenses)
        self.assertEqual(cat_data["Food & Dining"]["total"], 500.0)
        self.assertEqual(cat_data["Food & Dining"]["percentage"], 50.0)
        self.assertEqual(cat_data["Education & Books"]["total"], 500.0)
        self.assertEqual(cat_data["Education & Books"]["percentage"], 50.0)

    def test_budget_threshold_alerts(self):
        budget = MonthlyBudget("2026-09", 1000.0, {"Food & Dining": 500.0})

        # Under 80%
        healthy_exp = [Expense("1", "2026-09-01", 300.0, "Food & Dining", "Groceries")]
        res = analytics.calculate_budget_analytics(healthy_exp, "2026-09", budget)
        self.assertEqual(res["overall_status"], "HEALTHY")
        self.assertEqual(res["categories"]["Food & Dining"]["status"], "HEALTHY")

        # Warning (> 80%)
        warn_exp = [Expense("1", "2026-09-01", 850.0, "Food & Dining", "Party")]
        res_warn = analytics.calculate_budget_analytics(warn_exp, "2026-09", budget)
        self.assertEqual(res_warn["overall_status"], "WARNING")
        self.assertEqual(res_warn["categories"]["Food & Dining"]["status"], "EXCEEDED")

        # Exceeded (> 100%)
        over_exp = [Expense("1", "2026-09-01", 1200.0, "Food & Dining", "Banquet")]
        res_over = analytics.calculate_budget_analytics(over_exp, "2026-09", budget)
        self.assertEqual(res_over["overall_status"], "OVER_BUDGET")

    def test_ascii_bar_rendering(self):
        bar_empty = analytics.render_ascii_bar(0.0, width=10)
        self.assertEqual(bar_empty, "[----------]")

        bar_full = analytics.render_ascii_bar(100.0, width=10)
        self.assertEqual(bar_full, "[==========]")

        bar_half = analytics.render_ascii_bar(50.0, width=10)
        self.assertEqual(bar_half, "[=====-----]")


class TestExpenseTrackerOperations(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_tracker_")
        self.tracker = ExpenseTracker(data_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_crud_lifecycle(self):
        # 1. Create
        exp = self.tracker.record_expense("2026-09-10", 250.0, "Transportation", "Metro Commute", "UPI")
        self.assertIsNotNone(exp.id)

        # 2. Read
        found = self.tracker.find_by_id(exp.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, 250.0)

        # 3. Update
        self.tracker.update_expense(exp.id, amount=300.0, description="Metro + Bus")
        updated = self.tracker.find_by_id(exp.id)
        self.assertEqual(updated.amount, 300.0)
        self.assertEqual(updated.description, "Metro + Bus")

        # 4. Filter
        filtered = self.tracker.filter_expenses(category="Transportation")
        self.assertTrue(any(e.id == exp.id for e in filtered))

        # 5. Delete
        self.tracker.delete_expense(exp.id)
        self.assertIsNone(self.tracker.find_by_id(exp.id))


if __name__ == "__main__":
    unittest.main()
