from pathlib import Path

from config import FINANCE_SALARIES_FILE, FINANCE_TRANSACTIONS_FILE
from services.finance_ops_service import add_transaction, get_salary_setup, get_transactions, upsert_salary_setup


def test_add_transaction_and_read_back_for_client():
    original = FINANCE_TRANSACTIONS_FILE.read_text() if FINANCE_TRANSACTIONS_FILE.exists() else ""
    try:
        ok, message = add_transaction(
            "demo_client",
            {
                "transaction_date": "2026-02-28",
                "transaction_type": "expense",
                "category": "salary",
                "title": "Salary payout",
                "notes": "Payroll for February",
                "amount": 1450,
            },
            actor_username="owner",
        )

        assert ok is True
        assert message == "Transaction added"

        tx = get_transactions("demo_client")
        assert not tx.empty
        assert (tx["title"] == "Salary payout").any()
    finally:
        Path(FINANCE_TRANSACTIONS_FILE).write_text(original)


def test_salary_setup_upsert_for_client():
    original = FINANCE_SALARIES_FILE.read_text() if FINANCE_SALARIES_FILE.exists() else ""
    try:
        ok, message = upsert_salary_setup(
            "demo_client",
            {
                "employee_name": "Jane Doe",
                "role_title": "Cashier",
                "monthly_salary": 850,
                "payment_day": 25,
                "status": "active",
            },
        )

        assert ok is True
        assert message == "Salary setup added"

        rows = get_salary_setup("demo_client")
        assert not rows.empty
        assert (rows["employee_name"] == "Jane Doe").any()
    finally:
        Path(FINANCE_SALARIES_FILE).write_text(original)
