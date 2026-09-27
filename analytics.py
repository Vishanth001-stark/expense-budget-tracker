"""
analytics.py
CLI Analytics engine: Category-wise spending aggregation, real-time budget tracking,
ASCII visual progress charts, and financial analytics.
"""

from typing import List, Dict, Any, Optional
from models import Expense, MonthlyBudget


def aggregate_by_category(expenses: List[Expense]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregates expenses by category.
    Returns: Dict mapping category -> { 'total': float, 'count': int, 'percentage': float }
    """
    total_spend = sum(e.amount for e in expenses)
    cat_data: Dict[str, Dict[str, Any]] = {}

    for exp in expenses:
        if exp.category not in cat_data:
            cat_data[exp.category] = {"total": 0.0, "count": 0, "percentage": 0.0}
        cat_data[exp.category]["total"] += exp.amount
        cat_data[exp.category]["count"] += 1

    if total_spend > 0:
        for cat in cat_data:
            cat_data[cat]["percentage"] = round((cat_data[cat]["total"] / total_spend) * 100.0, 1)

    # Sort descending by total spent
    return dict(sorted(cat_data.items(), key=lambda item: item[1]["total"], reverse=True))


def filter_by_month(expenses: List[Expense], month_str: str) -> List[Expense]:
    """
    Filters expenses belonging to a specific month (YYYY-MM).
    """
    return [e for e in expenses if e.date.startswith(month_str)]


def calculate_budget_analytics(
    expenses: List[Expense],
    month_str: str,
    budget: Optional[MonthlyBudget]
) -> Dict[str, Any]:
    """
    Generates real-time budget analytics for a given month.
    """
    month_expenses = filter_by_month(expenses, month_str)
    total_spent = sum(e.amount for e in month_expenses)
    cat_breakdown = aggregate_by_category(month_expenses)

    overall_limit = budget.overall_limit if budget else 0.0
    overall_spent_pct = round((total_spent / overall_limit) * 100.0, 1) if overall_limit > 0 else 0.0
    remaining_balance = round(overall_limit - total_spent, 2) if overall_limit > 0 else 0.0

    category_statuses: Dict[str, Dict[str, Any]] = {}
    category_limits = budget.category_limits if budget else {}

    for cat, data in cat_breakdown.items():
        limit = category_limits.get(cat, 0.0)
        spent = data["total"]
        pct = round((spent / limit) * 100.0, 1) if limit > 0 else 0.0
        remaining = round(limit - spent, 2) if limit > 0 else 0.0

        status = "No Limit"
        if limit > 0:
            if spent > limit:
                status = "EXCEEDED"
            elif pct >= 80.0:
                status = "WARNING"
            else:
                status = "HEALTHY"

        category_statuses[cat] = {
            "spent": spent,
            "limit": limit,
            "percentage": pct,
            "remaining": remaining,
            "status": status,
            "count": data["count"]
        }

    # Also capture categories that have a budget set but zero expenditure so far
    for cat, limit in category_limits.items():
        if cat not in category_statuses and limit > 0:
            category_statuses[cat] = {
                "spent": 0.0,
                "limit": limit,
                "percentage": 0.0,
                "remaining": limit,
                "status": "HEALTHY",
                "count": 0
            }

    overall_status = "No Budget Set"
    if overall_limit > 0:
        if total_spent > overall_limit:
            overall_status = "OVER_BUDGET"
        elif overall_spent_pct >= 80.0:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"

    return {
        "month": month_str,
        "total_spent": round(total_spent, 2),
        "overall_limit": overall_limit,
        "overall_spent_pct": overall_spent_pct,
        "remaining_balance": remaining_balance,
        "overall_status": overall_status,
        "expense_count": len(month_expenses),
        "categories": category_statuses
    }


def render_ascii_bar(percentage: float, width: int = 24) -> str:
    """
    Renders an ASCII progress bar for CLI visualization.
    e.g. [====================----]
    """
    clamped = max(0.0, min(percentage, 100.0))
    filled_len = int(round(width * (clamped / 100.0)))
    empty_len = width - filled_len
    bar = "=" * filled_len + "-" * empty_len
    return f"[{bar}]"


def get_financial_summary_metrics(expenses: List[Expense]) -> Dict[str, Any]:
    """
    Computes comprehensive high-level metrics across all recorded expenses.
    """
    if not expenses:
        return {
            "total_expenses": 0,
            "total_spend": 0.0,
            "average_expense": 0.0,
            "highest_expense": None,
            "lowest_expense": None,
            "most_frequent_category": "N/A"
        }

    total_spend = sum(e.amount for e in expenses)
    avg_expense = round(total_spend / len(expenses), 2)
    sorted_by_amt = sorted(expenses, key=lambda x: x.amount, reverse=True)
    cat_counts: Dict[str, int] = {}
    for e in expenses:
        cat_counts[e.category] = cat_counts.get(e.category, 0) + 1
    top_cat = max(cat_counts.items(), key=lambda x: x[1])[0] if cat_counts else "N/A"

    return {
        "total_expenses": len(expenses),
        "total_spend": round(total_spend, 2),
        "average_expense": avg_expense,
        "highest_expense": sorted_by_amt[0],
        "lowest_expense": sorted_by_amt[-1],
        "most_frequent_category": top_cat
    }
