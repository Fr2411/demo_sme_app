from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from config import FINANCE_SALARIES_FILE, FINANCE_TRANSACTIONS_FILE
from services.client_service import ensure_db_structure

TRANSACTION_COLUMNS = [
    "client_id",
    "created_at",
    "transaction_date",
    "transaction_type",
    "category",
    "title",
    "notes",
    "amount",
    "created_by",
]

SALARY_COLUMNS = [
    "client_id",
    "employee_name",
    "role_title",
    "monthly_salary",
    "payment_day",
    "status",
    "updated_at",
]


DEFAULT_EXPENSE_CATEGORIES = ["inventory", "salary", "rent", "utility", "marketing", "logistics", "other"]
DEFAULT_INCOME_CATEGORIES = ["sales", "service", "refund", "other"]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_csv(path, columns: list[str]) -> pd.DataFrame:
    ensure_db_structure()
    df = pd.read_csv(path, dtype=str)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def get_transactions(client_id: str) -> pd.DataFrame:
    df = _load_csv(FINANCE_TRANSACTIONS_FILE, TRANSACTION_COLUMNS)
    scoped = df[df["client_id"].astype(str) == str(client_id)].copy()
    if scoped.empty:
        return scoped

    scoped["amount"] = pd.to_numeric(scoped["amount"], errors="coerce").fillna(0.0)
    scoped["transaction_date"] = pd.to_datetime(scoped["transaction_date"], errors="coerce")
    scoped = scoped.sort_values(["transaction_date", "created_at"], ascending=[False, False])
    return scoped


def add_transaction(client_id: str, payload: dict, actor_username: str) -> tuple[bool, str]:
    transaction_type = str(payload.get("transaction_type", "expense")).strip().lower()
    if transaction_type not in {"expense", "income"}:
        return False, "Transaction type must be expense or income"

    amount = _safe_float(payload.get("amount"), default=-1)
    if amount <= 0:
        return False, "Amount must be greater than zero"

    transaction_date = str(payload.get("transaction_date", "")).strip()
    title = str(payload.get("title", "")).strip()
    category = str(payload.get("category", "other")).strip().lower()

    if not transaction_date:
        return False, "Transaction date is required"
    if not title:
        return False, "Title is required"

    records = _load_csv(FINANCE_TRANSACTIONS_FILE, TRANSACTION_COLUMNS)
    row = {
        "client_id": str(client_id),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_date": transaction_date,
        "transaction_type": transaction_type,
        "category": category,
        "title": title,
        "notes": str(payload.get("notes", "")).strip(),
        "amount": f"{amount:.2f}",
        "created_by": str(actor_username).strip(),
    }
    records = pd.concat([records, pd.DataFrame([row], columns=TRANSACTION_COLUMNS)], ignore_index=True)
    records.to_csv(FINANCE_TRANSACTIONS_FILE, index=False)
    return True, "Transaction added"


def get_salary_setup(client_id: str) -> pd.DataFrame:
    df = _load_csv(FINANCE_SALARIES_FILE, SALARY_COLUMNS)
    scoped = df[df["client_id"].astype(str) == str(client_id)].copy()
    if scoped.empty:
        return scoped

    scoped["monthly_salary"] = pd.to_numeric(scoped["monthly_salary"], errors="coerce").fillna(0.0)
    scoped["payment_day"] = pd.to_numeric(scoped["payment_day"], errors="coerce").fillna(1).astype(int)
    scoped = scoped.sort_values(["status", "employee_name"], ascending=[True, True])
    return scoped


def upsert_salary_setup(client_id: str, payload: dict) -> tuple[bool, str]:
    employee_name = str(payload.get("employee_name", "")).strip()
    role_title = str(payload.get("role_title", "")).strip()
    monthly_salary = _safe_float(payload.get("monthly_salary"), default=-1)
    payment_day = int(_safe_float(payload.get("payment_day"), default=0))
    status = str(payload.get("status", "active")).strip().lower()

    if not employee_name:
        return False, "Employee name is required"
    if monthly_salary <= 0:
        return False, "Monthly salary must be greater than zero"
    if payment_day < 1 or payment_day > 31:
        return False, "Payment day must be between 1 and 31"
    if status not in {"active", "inactive"}:
        return False, "Status must be active or inactive"

    salaries = _load_csv(FINANCE_SALARIES_FILE, SALARY_COLUMNS)
    mask = (salaries["client_id"].astype(str) == str(client_id)) & (
        salaries["employee_name"].astype(str).str.lower() == employee_name.lower()
    )

    row = {
        "client_id": str(client_id),
        "employee_name": employee_name,
        "role_title": role_title,
        "monthly_salary": f"{monthly_salary:.2f}",
        "payment_day": str(payment_day),
        "status": status,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    if mask.any():
        for key, value in row.items():
            salaries.loc[mask, key] = value
        message = "Salary setup updated"
    else:
        salaries = pd.concat([salaries, pd.DataFrame([row], columns=SALARY_COLUMNS)], ignore_index=True)
        message = "Salary setup added"

    salaries.to_csv(FINANCE_SALARIES_FILE, index=False)
    return True, message
