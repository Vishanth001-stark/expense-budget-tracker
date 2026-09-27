"""
tracker.py
Core controller coordinating expenses, budget rules, CSV persistence, and CLI analytics.
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from models import Expense, MonthlyBudget
from storage import StorageManager
import analytics


class ExpenseTracker:
    """
    Coordinates CRUD operations, structured validation, budget management,
    and analytics reporting.
    """

    def __init__(self, data_dir: str = "data"):
        self.storage = StorageManager(data_dir=data_dir)
        self.expenses: List[Expense] = []
        self.budgets: Dict[str, MonthlyBudget] = {}
        self.load()

    def load(self) -> Tuple[int, int]:
        loaded_exp, corrupt_count = self.storage.load_expenses()
        self.expenses = loaded_exp
        self.budgets = self.storage.load_budgets()

        # If clean install with no records, seed initial demo data
        if not self.expenses and not self.budgets:
            self.expenses, self.budgets = self.storage.seed_initial_data()

        return len(self.expenses), corrupt_count

    def save(self) -> bool:
        ok1 = self.storage.save_expenses(self.expenses)
        ok2 = self.storage.save_budgets(self.budgets)
        return ok1 and ok2

    def _generate_next_id(self) -> str:
        max_num = 1000
        for exp in self.expenses:
            if exp.id.startswith("EXP-"):
                try:
                    num = int(exp.id.split("-")[1])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
        return f"EXP-{max_num + 1}"

    def record_expense(
        self,
        date_str: str,
        amount: float,
        category: str,
        description: str,
        payment_method: str = "UPI"
    ) -> Expense:
        new_id = self._generate_next_id()
        expense = Expense(
            id=new_id,
            date=date_str,
            amount=amount,
            category=category,
            description=description,
            payment_method=payment_method
        )
        self.expenses.append(expense)
        # Keep sorted by date descending (latest first)
        self.expenses.sort(key=lambda x: (x.date, x.id), reverse=True)
        self.save()
        return expense

    def find_by_id(self, exp_id: str) -> Optional[Expense]:
        target = exp_id.strip().upper()
        for e in self.expenses:
            if e.id.upper() == target:
                return e
        return None

    def update_expense(
        self,
        exp_id: str,
        date_str: Optional[str] = None,
        amount: Optional[float] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> bool:
        exp = self.find_by_id(exp_id)
        if not exp:
            return False

        if date_str: exp.date = date_str
        if amount is not None and amount > 0: exp.amount = amount
        if category: exp.category = category
        if description: exp.description = description
        if payment_method: exp.payment_method = payment_method

        self.expenses.sort(key=lambda x: (x.date, x.id), reverse=True)
        self.save()
        return True

    def delete_expense(self, exp_id: str) -> bool:
        exp = self.find_by_id(exp_id)
        if not exp:
            return False

        self.expenses = [e for e in self.expenses if e.id.upper() != exp_id.strip().upper()]
        self.save()
        return True

    def set_budget(
        self,
        month_str: str,
        overall_limit: float,
        category_limits: Optional[Dict[str, float]] = None
    ) -> MonthlyBudget:
        budget = MonthlyBudget(
            month=month_str,
            overall_limit=overall_limit,
            category_limits=category_limits or {}
        )
        self.budgets[month_str] = budget
        self.save()
        return budget

    def get_budget(self, month_str: str) -> Optional[MonthlyBudget]:
        return self.budgets.get(month_str)

    def filter_expenses(
        self,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[Expense]:
        results = self.expenses

        if category:
            results = [e for e in results if e.category.lower() == category.lower()]
        if payment_method:
            results = [e for e in results if e.payment_method.lower() == payment_method.lower()]
        if start_date:
            results = [e for e in results if e.date >= start_date]
        if end_date:
            results = [e for e in results if e.date <= end_date]
        if keyword:
            kw = keyword.lower()
            results = [
                e for e in results
                if kw in e.description.lower() or kw in e.category.lower() or kw in e.id.lower()
            ]

        return results

    def get_month_analytics(self, month_str: Optional[str] = None) -> Dict[str, Any]:
        target_month = month_str or datetime.now().strftime("%Y-%m")
        budget = self.get_budget(target_month)
        return analytics.calculate_budget_analytics(self.expenses, target_month, budget)

    def export_summary_text(self, month_str: Optional[str] = None) -> str:
        report_month = month_str or datetime.now().strftime("%Y-%m")
        stats = self.get_month_analytics(report_month)

        lines = [
            "=" * 70,
            f"          FINANCIAL EXPENDITURE & BUDGET REPORT ({report_month})",
            "=" * 70,
            f"  Total Spend       : Rs. {stats['total_spent']:,.2f}",
            f"  Overall Budget    : Rs. {stats['overall_limit']:,.2f}" if stats['overall_limit'] > 0 else "  Overall Budget    : Not Set",
            f"  Budget Consumed   : {stats['overall_spent_pct']:.1f}%",
            f"  Remaining Balance : Rs. {stats['remaining_balance']:,.2f}",
            f"  Budget Status     : {stats['overall_status']}",
            f"  Total Transactions: {stats['expense_count']}",
            "-" * 70,
            "  CATEGORY BREAKDOWN:",
            f"  {'Category':<24} {'Spent (Rs.)':<14} {'Limit (Rs.)':<14} {'Status':<10}"
        ]

        for cat, data in stats["categories"].items():
            limit_str = f"{data['limit']:,.2f}" if data['limit'] > 0 else "-"
            lines.append(f"  {cat:<24} {data['spent']:<14,.2f} {limit_str:<14} {data['status']:<10}")

        lines.append("=" * 70)
        return "\n".join(lines)
