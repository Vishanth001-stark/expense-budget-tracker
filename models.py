"""
models.py
Domain models representing Expenses and Budgets.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any


VALID_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Education & Books",
    "Tech & Software",
    "Entertainment",
    "Utilities & Bills",
    "Healthcare",
    "Shopping & Personal",
    "Other"
]

VALID_PAYMENT_METHODS = [
    "UPI",
    "Debit Card",
    "Credit Card",
    "Cash",
    "Net Banking"
]


@dataclass
class Expense:
    id: str
    date: str  # Format: YYYY-MM-DD
    amount: float
    category: str
    description: str
    payment_method: str = "UPI"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "amount": f"{self.amount:.2f}",
            "category": self.category,
            "description": self.description,
            "payment_method": self.payment_method,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expense":
        return cls(
            id=str(data.get("id", "")).strip(),
            date=str(data.get("date", "")).strip(),
            amount=float(data.get("amount", 0.0)),
            category=str(data.get("category", "Other")).strip(),
            description=str(data.get("description", "")).strip(),
            payment_method=str(data.get("payment_method", "UPI")).strip(),
            created_at=str(data.get("created_at", datetime.now().isoformat())).strip()
        )


@dataclass
class MonthlyBudget:
    month: str  # Format: YYYY-MM
    overall_limit: float
    category_limits: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # Serialized category limits as cat1:limit1;cat2:limit2
        cat_str = ";".join(f"{k}:{v:.2f}" for k, v in self.category_limits.items())
        return {
            "month": self.month,
            "overall_limit": f"{self.overall_limit:.2f}",
            "category_limits": cat_str
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonthlyBudget":
        cat_map: Dict[str, float] = {}
        raw_cats = str(data.get("category_limits", "")).strip()
        if raw_cats:
            for item in raw_cats.split(";"):
                if ":" in item:
                    k, v = item.split(":", 1)
                    try:
                        cat_map[k.strip()] = float(v.strip())
                    except ValueError:
                        pass
        return cls(
            month=str(data.get("month", "")).strip(),
            overall_limit=float(data.get("overall_limit", 0.0)),
            category_limits=cat_map
        )
