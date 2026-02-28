from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.rbac import require_roles
from backend.app.db.session import get_db
from backend.app.schemas.finance import (
    BalanceSheetReport,
    CashflowReport,
    EmployeeCreate,
    EmployeeRead,
    ExpenseCreate,
    ExpenseRead,
    FinanceDashboardSummary,
    IncomeCreate,
    IncomeRead,
    PayrollApprove,
    PayrollCreate,
    PayrollRead,
    ProfitLossReport,
)
from backend.app.services.finance_service import (
    approve_and_pay_payroll,
    create_employee,
    finance_dashboard_summary,
    generate_balance_sheet,
    generate_cashflow_report,
    generate_profit_loss_report,
    process_payroll,
    record_expense,
    record_income,
)

router = APIRouter(prefix='/finance', tags=['finance'])


def _assert_finance_read_access(user=Depends(get_current_user)):
    role_names = {r.name for r in user.roles}
    if not role_names.intersection({'admin'}):
        raise HTTPException(status_code=403, detail='No financial read access')
    return user


@router.post('/expenses', response_model=ExpenseRead)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles('admin')),
):
    return record_expense(db, payload, user)


@router.post('/income', response_model=IncomeRead)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles('admin')),
):
    return record_income(db, payload, user)


@router.post('/employees', response_model=EmployeeRead)
def create_employee_record(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles('admin')),
):
    return create_employee(db, payload, user)


@router.post('/payroll', response_model=PayrollRead)
def create_payroll(
    payload: PayrollCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles('admin')),
):
    return process_payroll(db, payload, user)


@router.post('/payroll/{payroll_id}/approve', response_model=PayrollRead)
def approve_payroll(
    payroll_id: int,
    payload: PayrollApprove,
    db: Session = Depends(get_db),
    user=Depends(require_roles('admin')),
):
    return approve_and_pay_payroll(db, payroll_id, payload.otp_code, user)


@router.get('/reports/cashflow', response_model=CashflowReport)
def get_cashflow_report(start_date: date, end_date: date, db: Session = Depends(get_db), _=Depends(_assert_finance_read_access)):
    return generate_cashflow_report(db, start_date, end_date)


@router.get('/reports/pnl', response_model=ProfitLossReport)
def get_profit_loss_report(start_date: date, end_date: date, db: Session = Depends(get_db), _=Depends(_assert_finance_read_access)):
    return generate_profit_loss_report(db, start_date, end_date)


@router.get('/reports/balance-sheet', response_model=BalanceSheetReport)
def get_balance_sheet(as_of_date: date, db: Session = Depends(get_db), _=Depends(_assert_finance_read_access)):
    return generate_balance_sheet(db, as_of_date)


@router.get('/dashboard', response_model=FinanceDashboardSummary)
def get_finance_dashboard(db: Session = Depends(get_db), _=Depends(_assert_finance_read_access)):
    return finance_dashboard_summary(db)
