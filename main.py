"""
main.py
Interactive Command-Line Interface for Personal Expense & Budget Tracker.
Demonstrates Python modularity, CSV persistence, and CLI analytics.
Author: Vishanth R
"""

import sys
from datetime import datetime
from typing import List, Optional

# Ensure safe UTF-8 terminal encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from models import Expense, VALID_CATEGORIES, VALID_PAYMENT_METHODS
from tracker import ExpenseTracker
from validators import (
    validate_date,
    validate_month,
    validate_amount,
    validate_category,
    validate_payment_method,
    validate_description
)
import analytics


def clear_screen():
    # Keep output visible across terminals
    pass


def print_banner():
    print("=" * 80)
    print("                PERSONAL EXPENSE & BUDGET TRACKER")
    print("         Python CLI Analytics  |  Modular CSV Data Persistence")
    print("                     Author: Vishanth R")
    print("=" * 80)


def print_menu():
    print("\n------------------------------ MAIN MENU ---------------------------------------")
    print(" 1. Record New Daily Expenditure")
    print(" 2. View All Expenses (Tabular Log)")
    print(" 3. Category-Wise Spending Analytics & ASCII Visual Chart")
    print(" 4. Real-Time Monthly Budget Tracker & Threshold Alerts")
    print(" 5. Search & Filter Expenses (Category / Date / Method / Keyword)")
    print(" 6. Configure Monthly Budget & Category Ceilings")
    print(" 7. Modify or Delete an Expense Record")
    print(" 8. High-Level All-Time Financial Metrics")
    print(" 9. Export Monthly Report to Text File")
    print(" 10. Save & Exit Application")
    print("--------------------------------------------------------------------------------")


def format_table(expenses: List[Expense]):
    if not expenses:
        print("\n[i] No expenses found matching criteria.\n")
        return

    print("\n" + "=" * 94)
    print(f"{'ID':<10} | {'Date':<11} | {'Category':<20} | {'Amount (Rs)':<12} | {'Method':<11} | {'Description':<20}")
    print("-" * 10 + "-+-" + "-" * 11 + "-+-" + "-" * 20 + "-+-" + "-" * 12 + "-+-" + "-" * 11 + "-+-" + "-" * 20)

    for e in expenses:
        desc_trunc = e.description if len(e.description) <= 20 else e.description[:17] + "..."
        print(f"{e.id:<10} | {e.date:<11} | {e.category:<20} | {e.amount:>11.2f} | {e.payment_method:<11} | {desc_trunc:<20}")

    print("=" * 94)
    total_val = sum(e.amount for e in expenses)
    print(f"Total Count: {len(expenses)} item(s)  |  Cumulative Sum: Rs. {total_val:,.2f}\n")


def handle_record_expense(tracker: ExpenseTracker):
    print("\n>>> RECORD NEW DAILY EXPENDITURE")

    # Date
    while True:
        date_in = input("Enter Date (YYYY-MM-DD or 'today'): ").strip()
        ok, parsed_date, err = validate_date(date_in)
        if ok:
            break
        print(f"[!] {err}")

    # Amount
    while True:
        amt_in = input("Enter Amount in Rs (e.g. 250.00): ").strip()
        ok, parsed_amt, err = validate_amount(amt_in)
        if ok:
            break
        print(f"[!] {err}")

    # Category Selection
    print("\nSelect Category:")
    for idx, cat in enumerate(VALID_CATEGORIES, 1):
        print(f"  {idx}. {cat}")
    while True:
        cat_in = input(f"Enter Category number (1-{len(VALID_CATEGORIES)}) or name: ").strip()
        ok, parsed_cat, err = validate_category(cat_in)
        if ok:
            break
        print(f"[!] {err}")

    # Payment Method Selection
    print("\nSelect Payment Method:")
    for idx, pm in enumerate(VALID_PAYMENT_METHODS, 1):
        print(f"  {idx}. {pm}")
    while True:
        pm_in = input(f"Enter Payment Method (1-{len(VALID_PAYMENT_METHODS)}) [Default: 1 (UPI)]: ").strip()
        if not pm_in:
            parsed_pm = "UPI"
            break
        ok, parsed_pm, err = validate_payment_method(pm_in)
        if ok:
            break
        print(f"[!] {err}")

    # Description
    while True:
        desc_in = input("Enter Description / Notes: ").strip()
        ok, parsed_desc, err = validate_description(desc_in)
        if ok:
            break
        print(f"[!] {err}")

    new_exp = tracker.record_expense(
        date_str=parsed_date,
        amount=parsed_amt,
        category=parsed_cat,
        description=parsed_desc,
        payment_method=parsed_pm
    )

    print(f"\n[SUCCESS] Expense recorded successfully! Assigned ID: {new_exp.id}")

    # Check immediate budget status for this month
    month_str = parsed_date[:7]
    month_stats = tracker.get_month_analytics(month_str)
    if month_stats["overall_status"] == "OVER_BUDGET":
        print(f"[!] ALERT: Monthly budget for {month_str} is EXCEEDED! (Rs. {month_stats['total_spent']:,.2f} / Rs. {month_stats['overall_limit']:,.2f})")
    elif month_stats["overall_status"] == "WARNING":
        print(f"[!] NOTICE: Monthly spending has crossed 80% threshold! ({month_stats['overall_spent_pct']:.1f}%)")


def handle_category_analytics(tracker: ExpenseTracker):
    print("\n>>> CATEGORY-WISE SPENDING ANALYTICS")
    target_month = input("Enter Month (YYYY-MM or 'all' / 'current') [Default: current]: ").strip()
    if not target_month or target_month.lower() in ("current", "c"):
        target_month = datetime.now().strftime("%Y-%m")
        expenses = analytics.filter_by_month(tracker.expenses, target_month)
        title = f"Category Spending for {target_month}"
    elif target_month.lower() == "all":
        expenses = tracker.expenses
        title = "All-Time Category Spending"
    else:
        ok, parsed_month, err = validate_month(target_month)
        if not ok:
            print(f"[!] {err}")
            return
        expenses = analytics.filter_by_month(tracker.expenses, parsed_month)
        title = f"Category Spending for {parsed_month}"

    if not expenses:
        print(f"\n[i] No expenses recorded for the selected period.\n")
        return

    cat_breakdown = analytics.aggregate_by_category(expenses)
    total_spent = sum(e.amount for e in expenses)

    print("\n" + "=" * 80)
    print(f"  {title.upper()} (Total Spend: Rs. {total_spent:,.2f})")
    print("=" * 80)
    print(f"  {'Category':<22} | {'Amount (Rs)':<12} | {'Share':<7} | {'Visual ASCII Distribution'}")
    print("  " + "-" * 22 + "-+-" + "-" * 12 + "-+-" + "-" * 7 + "-+-" + "-" * 30)

    for cat, data in cat_breakdown.items():
        bar = analytics.render_ascii_bar(data["percentage"], width=24)
        print(f"  {cat:<22} | {data['total']:>12.2f} | {data['percentage']:>6.1f}% | {bar}")

    print("=" * 80 + "\n")


def handle_budget_tracker(tracker: ExpenseTracker):
    print("\n>>> REAL-TIME MONTHLY BUDGET TRACKER")
    month_in = input("Enter Month to inspect (YYYY-MM or 'current') [Default: current]: ").strip()
    if not month_in:
        month_in = "current"

    ok, target_month, err = validate_month(month_in)
    if not ok:
        print(f"[!] {err}")
        return

    stats = tracker.get_month_analytics(target_month)

    print("\n" + "=" * 80)
    print(f"             BUDGET HEALTH & ANALYTICS REPORT ({target_month})")
    print("=" * 80)
    print(f"  Monthly Expenditure : Rs. {stats['total_spent']:,.2f}")
    if stats['overall_limit'] > 0:
        print(f"  Overall Budget Cap  : Rs. {stats['overall_limit']:,.2f}")
        print(f"  Remaining Allowance : Rs. {stats['remaining_balance']:,.2f}")
        print(f"  Budget Consumption  : {stats['overall_spent_pct']:.1f}%")
        bar = analytics.render_ascii_bar(stats['overall_spent_pct'], width=28)
        print(f"  Overall Utilization : {bar}")

        # Alert level
        if stats['overall_status'] == "OVER_BUDGET":
            print("  ALERT STATUS        : [CRITICAL: OVER BUDGET! Please curtail non-essential spending]")
        elif stats['overall_status'] == "WARNING":
            print("  ALERT STATUS        : [CAUTION: Above 80% threshold!]")
        else:
            print("  ALERT STATUS        : [HEALTHY: Spending is within planned limits]")
    else:
        print("  Overall Budget Cap  : [Not set yet. Use Option 6 to establish limits]")

    print("-" * 80)
    print("  CATEGORY-LEVEL BUDGETS & THRESHOLDS:")
    print(f"  {'Category':<22} | {'Spent (Rs)':<11} | {'Limit (Rs)':<11} | {'Used %':<7} | {'Status'}")
    print("  " + "-" * 22 + "-+-" + "-" * 11 + "-+-" + "-" * 11 + "-+-" + "-" * 7 + "-+-" + "-" * 16)

    for cat, data in stats["categories"].items():
        lim_str = f"{data['limit']:,.2f}" if data['limit'] > 0 else "-"
        pct_str = f"{data['percentage']:.1f}%" if data['limit'] > 0 else "-"
        print(f"  {cat:<22} | {data['spent']:>11.2f} | {lim_str:>11} | {pct_str:>7} | [{data['status']}]")

    print("=" * 80 + "\n")


def handle_filter_expenses(tracker: ExpenseTracker):
    print("\n>>> SEARCH & FILTER EXPENSES")
    print("Press ENTER on any filter to skip it.\n")

    kw = input("Keyword search (description / category / ID): ").strip()
    cat_in = input(f"Category filter (or name, 1-{len(VALID_CATEGORIES)}): ").strip()
    cat_val = None
    if cat_in:
        ok, parsed_cat, _ = validate_category(cat_in)
        if ok: cat_val = parsed_cat

    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    start_val = None
    if start_date:
        ok, parsed_start, _ = validate_date(start_date)
        if ok: start_val = parsed_start

    end_date = input("End Date (YYYY-MM-DD): ").strip()
    end_val = None
    if end_date:
        ok, parsed_end, _ = validate_date(end_date)
        if ok: end_val = parsed_end

    method_in = input("Payment Method (UPI, Cash, Debit Card, etc.): ").strip()
    method_val = None
    if method_in:
        ok, parsed_method, _ = validate_payment_method(method_in)
        if ok: method_val = parsed_method

    results = tracker.filter_expenses(
        category=cat_val,
        payment_method=method_val,
        start_date=start_val,
        end_date=end_val,
        keyword=kw if kw else None
    )

    format_table(results)


def handle_configure_budget(tracker: ExpenseTracker):
    print("\n>>> CONFIGURE MONTHLY BUDGET LIMITS")
    month_in = input("Enter Target Month (YYYY-MM or 'current'): ").strip()
    if not month_in: month_in = "current"

    ok, target_month, err = validate_month(month_in)
    if not ok:
        print(f"[!] {err}")
        return

    current_budget = tracker.get_budget(target_month)
    current_limit = current_budget.overall_limit if current_budget else 0.0

    print(f"[i] Configuring Budget for {target_month} (Current: Rs. {current_limit:,.2f})")
    while True:
        limit_in = input("Enter Total Monthly Spending Cap in Rs: ").strip()
        ok, parsed_cap, err = validate_amount(limit_in)
        if ok: break
        print(f"[!] {err}")

    # Optional category limits
    cat_limits = {}
    print("\nWould you like to assign category-specific monthly ceilings? (y/n): ")
    assign_cats = input("> ").strip().lower()
    if assign_cats in ("y", "yes"):
        print("Enter ceiling in Rs for each category (or press ENTER to leave unconstrained):")
        for cat in VALID_CATEGORIES:
            val_in = input(f"  {cat} limit: ").strip()
            if val_in:
                ok, amt, _ = validate_amount(val_in)
                if ok:
                    cat_limits[cat] = amt

    tracker.set_budget(target_month, parsed_cap, cat_limits)
    print(f"\n[SUCCESS] Budget for {target_month} saved! Overall Cap: Rs. {parsed_cap:,.2f}")


def handle_modify_or_delete(tracker: ExpenseTracker):
    print("\n>>> MODIFY OR DELETE EXPENSE RECORD")
    exp_id = input("Enter Expense ID (e.g. EXP-1001): ").strip()
    expense = tracker.find_by_id(exp_id)

    if not expense:
        print(f"[ERROR] Expense ID '{exp_id}' not found.")
        return

    print("\nCurrent Record Details:")
    print(f"  ID: {expense.id} | Date: {expense.date} | Rs. {expense.amount:.2f} | Category: {expense.category}")
    print(f"  Method: {expense.payment_method} | Description: {expense.description}")

    action = input("\nChoose Action: (1) Modify, (2) Delete, (3) Cancel: ").strip()

    if action == "1":
        print("\nLeave blank to retain existing values.")
        date_in = input(f"New Date [{expense.date}]: ").strip()
        parsed_date = None
        if date_in:
            ok, p_date, _ = validate_date(date_in)
            if ok: parsed_date = p_date

        amt_in = input(f"New Amount [{expense.amount:.2f}]: ").strip()
        parsed_amt = None
        if amt_in:
            ok, p_amt, _ = validate_amount(amt_in)
            if ok: parsed_amt = p_amt

        desc_in = input(f"New Description [{expense.description}]: ").strip()
        parsed_desc = desc_in if desc_in else None

        cat_in = input(f"New Category [{expense.category}]: ").strip()
        parsed_cat = None
        if cat_in:
            ok, p_cat, _ = validate_category(cat_in)
            if ok: parsed_cat = p_cat

        pm_in = input(f"New Payment Method [{expense.payment_method}]: ").strip()
        parsed_pm = None
        if pm_in:
            ok, p_pm, _ = validate_payment_method(pm_in)
            if ok: parsed_pm = p_pm

        tracker.update_expense(
            exp_id=expense.id,
            date_str=parsed_date,
            amount=parsed_amt,
            category=parsed_cat,
            description=parsed_desc,
            payment_method=parsed_pm
        )
        print(f"[SUCCESS] Record {expense.id} updated successfully!")

    elif action == "2":
        confirm = input(f"Are you sure you want to delete {expense.id} (Rs. {expense.amount:.2f})? (y/n): ").strip().lower()
        if confirm in ("y", "yes"):
            tracker.delete_expense(expense.id)
            print(f"[SUCCESS] Record {expense.id} deleted.")
        else:
            print("[INFO] Deletion cancelled.")


def handle_all_time_metrics(tracker: ExpenseTracker):
    metrics = analytics.get_financial_summary_metrics(tracker.expenses)
    print("\n" + "=" * 70)
    print("            ALL-TIME FINANCIAL OVERVIEW & METRICS")
    print("=" * 70)
    print(f"  Total Transactions Logged : {metrics['total_expenses']}")
    print(f"  Cumulative Total Spend    : Rs. {metrics['total_spend']:,.2f}")
    print(f"  Average Expense Ticket    : Rs. {metrics['average_expense']:,.2f}")
    print(f"  Most Frequent Category    : {metrics['most_frequent_category']}")

    if metrics['highest_expense']:
        h = metrics['highest_expense']
        print(f"  Highest Single Expense    : Rs. {h.amount:,.2f} ({h.description} on {h.date})")

    if metrics['lowest_expense']:
        low = metrics['lowest_expense']
        print(f"  Lowest Single Expense     : Rs. {low.amount:,.2f} ({low.description} on {low.date})")

    print("=" * 70 + "\n")


def handle_export_report(tracker: ExpenseTracker):
    print("\n>>> EXPORT MONTHLY SUMMARY REPORT")
    month_in = input("Enter Month (YYYY-MM or 'current') [Default: current]: ").strip()
    if not month_in: month_in = "current"

    ok, target_month, err = validate_month(month_in)
    if not ok:
        print(f"[!] {err}")
        return

    content = tracker.export_summary_text(target_month)
    filename = f"report_{target_month}.txt"
    try:
        with open(filename, mode="w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n[SUCCESS] Financial report successfully exported to: {filename}\n")
        print(content)
    except Exception as e:
        print(f"[ERROR] Failed to write report: {e}")


def main():
    tracker = ExpenseTracker()
    print_banner()

    while True:
        print_menu()
        choice = input("Enter your choice (1-10): ").strip()

        if choice == "1":
            handle_record_expense(tracker)
        elif choice == "2":
            format_table(tracker.expenses)
        elif choice == "3":
            handle_category_analytics(tracker)
        elif choice == "4":
            handle_budget_tracker(tracker)
        elif choice == "5":
            handle_filter_expenses(tracker)
        elif choice == "6":
            handle_configure_budget(tracker)
        elif choice == "7":
            handle_modify_or_delete(tracker)
        elif choice == "8":
            handle_all_time_metrics(tracker)
        elif choice == "9":
            handle_export_report(tracker)
        elif choice == "10":
            tracker.save()
            print("\n[SUCCESS] All expense and budget changes committed to local CSV storage.")
            print("[INFO] Exiting Personal Expense & Budget Tracker. Goodbye!\n")
            sys.exit(0)
        else:
            print("\n[!] Invalid selection. Please choose an option from 1 to 10.")


if __name__ == "__main__":
    main()
