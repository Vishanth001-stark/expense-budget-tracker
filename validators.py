"""
validators.py
Input and data validation utilities for dates, numeric amounts, categories, and payment types.
"""

from datetime import datetime
from typing import Tuple, Optional, Any
from models import VALID_CATEGORIES, VALID_PAYMENT_METHODS


def validate_date(date_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates date string format YYYY-MM-DD or special shortcut 'today'.
    Returns: (is_valid, parsed_iso_date, error_message)
    """
    cleaned = date_str.strip()
    if cleaned.lower() in ("today", "t", "now"):
        return True, datetime.now().strftime("%Y-%m-%d"), None

    try:
        parsed = datetime.strptime(cleaned, "%Y-%m-%d")
        # Ensure year is reasonable
        if parsed.year < 2000 or parsed.year > 2100:
            return False, None, "Year must be between 2000 and 2100."
        return True, parsed.strftime("%Y-%m-%d"), None
    except ValueError:
        return False, None, "Invalid date format. Expected YYYY-MM-DD (e.g., 2026-09-27) or 'today'."


def validate_month(month_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates month string format YYYY-MM or 'current'.
    """
    cleaned = month_str.strip()
    if cleaned.lower() in ("current", "c", "now"):
        return True, datetime.now().strftime("%Y-%m"), None

    try:
        parsed = datetime.strptime(cleaned, "%Y-%m")
        return True, parsed.strftime("%Y-%m"), None
    except ValueError:
        return False, None, "Invalid month format. Expected YYYY-MM (e.g., 2026-09)."


def validate_amount(amount_input: Any) -> Tuple[bool, float, Optional[str]]:
    """
    Validates that the amount is a positive real number.
    """
    try:
        val = float(amount_input)
        if val <= 0:
            return False, 0.0, "Amount must be strictly greater than 0.00."
        if val > 10_000_000:
            return False, 0.0, "Amount exceeds realistic upper ceiling limit (10,000,000)."
        return True, round(val, 2), None
    except (ValueError, TypeError):
        return False, 0.0, "Amount must be a valid numeric number (e.g., 149.50)."


def validate_category(category_input: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates that the category matches one of the recognized categories
    or maps an integer index selection.
    """
    cleaned = category_input.strip()

    # Numeric selection (1-indexed)
    if cleaned.isdigit():
        idx = int(cleaned) - 1
        if 0 <= idx < len(VALID_CATEGORIES):
            return True, VALID_CATEGORIES[idx], None
        return False, "", f"Please select a number between 1 and {len(VALID_CATEGORIES)}."

    # Direct match or case-insensitive match
    for cat in VALID_CATEGORIES:
        if cat.lower() == cleaned.lower():
            return True, cat, None

    return False, "", f"Invalid category. Valid options: {', '.join(VALID_CATEGORIES)}"


def validate_payment_method(payment_input: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates payment method against allowed types.
    """
    cleaned = payment_input.strip()

    if cleaned.isdigit():
        idx = int(cleaned) - 1
        if 0 <= idx < len(VALID_PAYMENT_METHODS):
            return True, VALID_PAYMENT_METHODS[idx], None
        return False, "", f"Please select a number between 1 and {len(VALID_PAYMENT_METHODS)}."

    for method in VALID_PAYMENT_METHODS:
        if method.lower() == cleaned.lower():
            return True, method, None

    return False, "", f"Invalid payment method. Options: {', '.join(VALID_PAYMENT_METHODS)}"


def validate_description(description_input: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates description length and contents.
    """
    cleaned = description_input.strip()
    if not cleaned:
        return False, "", "Description cannot be empty."
    if len(cleaned) > 120:
        return False, "", "Description cannot exceed 120 characters."
    return True, cleaned, None
