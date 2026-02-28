from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.app.models.finance import Employee
from backend.app.services.finance_service import (
    generate_profit_loss_report,
    get_overdue_receivables,
    process_payroll,
)
from backend.app.schemas.finance import PayrollCreate


def monthly_payroll_generation(db: Session, system_user):
    today = date.today()
    period_start = today.replace(day=1)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    employees = db.query(Employee).filter(Employee.employment_status == 'active').all()
    records = []
    for employee in employees:
        records.append(
            process_payroll(
                db,
                PayrollCreate(
                    employee_id=employee.id,
                    period_start=period_start,
                    period_end=period_end,
                    bonus=0,
                    deductions=0,
                ),
                system_user,
            )
        )
    return records


def monthly_pnl_auto_snapshot(db: Session):
    today = date.today()
    start = today.replace(day=1)
    end = today
    return generate_profit_loss_report(db, start, end)


def overdue_receivable_alert(db: Session) -> list[dict]:
    overdue = get_overdue_receivables(db)
    return [{'invoice_id': item.id, 'customer_id': item.customer_id, 'due_date': item.due_date.isoformat()} for item in overdue]


def low_cash_warning_alert(db: Session, threshold: float = 5000.0) -> dict:
    from backend.app.services.finance_service import finance_dashboard_summary

    summary = finance_dashboard_summary(db)
    return {
        'is_low_cash': float(summary['current_cash_balance']) < threshold,
        'current_cash_balance': summary['current_cash_balance'],
        'threshold': threshold,
    }
