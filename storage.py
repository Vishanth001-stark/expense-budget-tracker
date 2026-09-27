"""
storage.py
Modular CSV parsing, atomic persistence, robust error handling, and backup operations.
"""

import csv
import os
import shutil
import tempfile
from typing import List, Dict, Tuple
from models import Expense, MonthlyBudget
from validators import validate_amount, validate_date


EXPENSES_CSV_FIELDS = [
    "id",
    "date",
    "amount",
    "category",
    "description",
    "payment_method",
    "created_at"
]

BUDGETS_CSV_FIELDS = [
    "month",
    "overall_limit",
    "category_limits"
]


class StorageManager:
    """
    Modular CSV storage manager with structured data validation,
    corrupted record recovery, and atomic file saving.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.expenses_file = os.path.join(data_dir, "expenses.csv")
        self.budgets_file = os.path.join(data_dir, "budgets.csv")
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)

    def load_expenses(self) -> Tuple[List[Expense], int]:
        """
        Loads and parses expense records from CSV.
        Returns: (valid_expenses, skipped_corrupt_count)
        """
        expenses: List[Expense] = []
        corrupted_count = 0

        if not os.path.exists(self.expenses_file):
            return expenses, 0

        try:
            with open(self.expenses_file, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                line_num = 1
                for row in reader:
                    line_num += 1
                    try:
                        # Validate mandatory fields
                        if not row.get("id") or not row.get("date") or not row.get("amount"):
                            corrupted_count += 1
                            continue

                        # Validate date
                        ok_date, parsed_date, _ = validate_date(str(row["date"]))
                        if not ok_date:
                            corrupted_count += 1
                            continue

                        # Validate amount
                        ok_amt, parsed_amt, _ = validate_amount(row["amount"])
                        if not ok_amt:
                            corrupted_count += 1
                            continue

                        exp = Expense(
                            id=row["id"].strip(),
                            date=parsed_date,
                            amount=parsed_amt,
                            category=row.get("category", "Other").strip() or "Other",
                            description=row.get("description", "").strip(),
                            payment_method=row.get("payment_method", "UPI").strip() or "UPI",
                            created_at=row.get("created_at", "").strip()
                        )
                        expenses.append(exp)
                    except Exception:
                        corrupted_count += 1
        except Exception as e:
            print(f"[Storage Warning] Could not open {self.expenses_file}: {e}")

        return expenses, corrupted_count

    def save_expenses(self, expenses: List[Expense]) -> bool:
        """
        Atomically saves expenses to CSV to prevent file corruption during mid-write interruptions.
        Creates a .backup snapshot first.
        """
        self._ensure_directories()

        # Step 1: Backup existing file if present
        if os.path.exists(self.expenses_file):
            backup_path = self.expenses_file + ".backup"
            try:
                shutil.copy2(self.expenses_file, backup_path)
            except OSError:
                pass

        # Step 2: Write to temporary file
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="expenses_tmp_", suffix=".csv")
        try:
            with os.fdopen(temp_fd, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=EXPENSES_CSV_FIELDS)
                writer.writeheader()
                for exp in expenses:
                    writer.writerow(exp.to_dict())

            # Step 3: Atomic replace
            shutil.move(temp_path, self.expenses_file)
            return True
        except Exception as e:
            print(f"[Storage Error] Failed to save expenses: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def load_budgets(self) -> Dict[str, MonthlyBudget]:
        """
        Loads monthly budget configurations from CSV.
        Returns: Dict mapping 'YYYY-MM' -> MonthlyBudget
        """
        budgets: Dict[str, MonthlyBudget] = {}
        if not os.path.exists(self.budgets_file):
            return budgets

        try:
            with open(self.budgets_file, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        b = MonthlyBudget.from_dict(row)
                        if b.month and b.overall_limit > 0:
                            budgets[b.month] = b
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Storage Warning] Could not load budgets: {e}")

        return budgets

    def save_budgets(self, budgets: Dict[str, MonthlyBudget]) -> bool:
        """
        Atomically saves monthly budgets to CSV.
        """
        self._ensure_directories()
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="budgets_tmp_", suffix=".csv")
        try:
            with os.fdopen(temp_fd, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=BUDGETS_CSV_FIELDS)
                writer.writeheader()
                for b in budgets.values():
                    writer.writerow(b.to_dict())

            shutil.move(temp_path, self.budgets_file)
            return True
        except Exception as e:
            print(f"[Storage Error] Failed to save budgets: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def seed_initial_data(self) -> Tuple[List[Expense], Dict[str, MonthlyBudget]]:
        """
        Seeds realistic expenses and monthly budget for Vishanth in Bengaluru.
        """
        demo_expenses = [
            Expense(id="EXP-1001", date="2026-09-02", amount=850.00, category="Education & Books", description="Algorithms & Data Structures Reference Handbook", payment_method="UPI"),
            Expense(id="EXP-1002", date="2026-09-04", amount=120.00, category="Transportation", description="Namma Metro SmartCard Recharge (Bengaluru Transit)", payment_method="UPI"),
            Expense(id="EXP-1003", date="2026-09-05", amount=340.00, category="Food & Dining", description="Campus Cafeteria Lunch & Refreshments", payment_method="UPI"),
            Expense(id="EXP-1004", date="2026-09-08", amount=799.00, category="Tech & Software", description="GitHub Pro & Cloud Developer Tool Subscription", payment_method="Debit Card"),
            Expense(id="EXP-1005", date="2026-09-10", amount=250.00, category="Transportation", description="Auto Commute to Jain University Campus", payment_method="Cash"),
            Expense(id="EXP-1006", date="2026-09-12", amount=560.00, category="Food & Dining", description="Weekend Study Group Dinner with Classmates", payment_method="UPI"),
            Expense(id="EXP-1007", date="2026-09-15", amount=450.00, category="Education & Books", description="Stationery, Lab Notebooks, and Circuit Components", payment_method="UPI"),
            Expense(id="EXP-1008", date="2026-09-18", amount=199.00, category="Entertainment", description="Weekend Streaming Subscription", payment_method="Debit Card"),
            Expense(id="EXP-1009", date="2026-09-20", amount=140.00, category="Transportation", description="Metro Commute to Hackathon Preparation Meetup", payment_method="UPI"),
            Expense(id="EXP-1010", date="2026-09-22", amount=620.00, category="Food & Dining", description="Hackathon Team Snacks & Energy Drinks", payment_method="UPI"),
            Expense(id="EXP-1011", date="2026-09-25", amount=300.00, category="Healthcare", description="Pharmacy multivitamins & medical checkup", payment_method="UPI"),
            Expense(id="EXP-1012", date="2026-09-27", amount=180.00, category="Food & Dining", description="Morning Breakfast & Filter Coffee", payment_method="UPI")
        ]

        # Monthly budget for 2026-09
        demo_budget = MonthlyBudget(
            month="2026-09",
            overall_limit=8000.00,
            category_limits={
                "Food & Dining": 2500.00,
                "Transportation": 1200.00,
                "Education & Books": 2000.00,
                "Tech & Software": 1200.00,
                "Entertainment": 600.00,
                "Healthcare": 500.00
            }
        )

        self.save_expenses(demo_expenses)
        self.save_budgets({"2026-09": demo_budget})
        return demo_expenses, {"2026-09": demo_budget}
