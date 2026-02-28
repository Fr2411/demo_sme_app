from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    category: str
    description: str | None = None
    vendor: str | None = None
    amount: Decimal = Field(gt=0)
    payment_method: str
    expense_date: date


class ExpenseRead(ExpenseCreate):
    id: int
    linked_journal_entry_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class IncomeCreate(BaseModel):
    source: str
    description: str | None = None
    amount: Decimal = Field(gt=0)
    payment_method: str
    income_date: date


class IncomeRead(IncomeCreate):
    id: int
    linked_journal_entry_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    full_name: str
    role_title: str
    base_salary: Decimal = Field(ge=0)
    hire_date: date
    employment_status: str = 'active'
    bank_account: str | None = None


class EmployeeRead(EmployeeCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollCreate(BaseModel):
    employee_id: int
    period_start: date
    period_end: date
    bonus: Decimal = Decimal('0')
    deductions: Decimal = Decimal('0')


class PayrollApprove(BaseModel):
    otp_code: str


class PayrollRead(BaseModel):
    id: int
    employee_id: int
    period_start: date
    period_end: date
    base_salary: Decimal
    bonus: Decimal
    deductions: Decimal
    net_salary: Decimal
    payment_status: str
    linked_journal_entry_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DateRangeQuery(BaseModel):
    start_date: date
    end_date: date


class CashflowReport(BaseModel):
    operating_cashflow: Decimal
    investing_cashflow: Decimal
    financing_cashflow: Decimal
    net_cashflow: Decimal


class ProfitLossReport(BaseModel):
    revenue: Decimal
    cogs: Decimal
    operating_expenses: Decimal
    salary_expense: Decimal
    net_profit: Decimal


class BalanceSheetReport(BaseModel):
    assets: Decimal
    liabilities: Decimal
    equity: Decimal


class FinanceDashboardSummary(BaseModel):
    current_cash_balance: Decimal
    total_receivables: Decimal
    total_payables: Decimal
    monthly_burn_rate: Decimal
    net_operating_cashflow: Decimal
    salary_obligations_next_30_days: Decimal
    revenue_this_month: Decimal
    expenses_this_month: Decimal
    net_profit_this_month: Decimal
