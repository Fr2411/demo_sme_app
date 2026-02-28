from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from backend.app.models.accounting import Account, JournalEntry, JournalLine
from backend.app.models.client import Invoice
from backend.app.models.finance import AuditLog, CashTransaction, Employee, Expense, Income, Payroll
from backend.app.models.user import User
from backend.app.schemas.finance import EmployeeCreate, ExpenseCreate, IncomeCreate, PayrollCreate


ACCOUNT_CODES = {
    'cash': '1000',
    'bank': '1010',
    'accounts_receivable': '1100',
    'accounts_payable': '2000',
    'revenue': '4000',
    'cogs': '5000',
    'operating_expense': '6000',
    'salary_expense': '6100',
    'payroll_liability': '2100',
    'owner_equity': '3000',
    'retained_earnings': '3100',
}


def _audit(db: Session, action: str, entity_type: str, entity_id: str, actor_user_id: int | None, metadata_json: str | None = None):
    db.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            metadata_json=metadata_json,
        )
    )


def _get_account_by_code(db: Session, code: str) -> Account:
    account = db.query(Account).filter(Account.code == code).first()
    if not account:
        raise HTTPException(status_code=400, detail=f'Account with code {code} not configured')
    return account


def ensure_default_chart_of_accounts(db: Session):
    defaults = [
        ('1000', 'Cash', 'asset'),
        ('1010', 'Bank', 'asset'),
        ('1100', 'Accounts Receivable', 'asset'),
        ('2000', 'Accounts Payable', 'liability'),
        ('2100', 'Payroll Liability', 'liability'),
        ('3000', 'Owner Equity', 'equity'),
        ('3100', 'Retained Earnings', 'equity'),
        ('4000', 'Revenue', 'revenue'),
        ('5000', 'Cost of Goods Sold', 'expense'),
        ('6000', 'Operating Expenses', 'expense'),
        ('6100', 'Salary Expense', 'expense'),
    ]
    for code, name, account_type in defaults:
        if not db.query(Account).filter(Account.code == code).first():
            db.add(Account(code=code, name=name, account_type=account_type))
    db.flush()


def create_balanced_journal_entry(
    db: Session,
    *,
    entry_date: date,
    description: str,
    reference_type: str,
    reference_id: str,
    lines: list[dict],
    created_by: int | None,
) -> JournalEntry:
    debit_total = sum((Decimal(line.get('debit', 0)) for line in lines), Decimal('0'))
    credit_total = sum((Decimal(line.get('credit', 0)) for line in lines), Decimal('0'))
    if debit_total != credit_total:
        raise HTTPException(status_code=400, detail='Journal entry not balanced')

    entry = JournalEntry(
        entry_date=entry_date.isoformat(),
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )
    db.add(entry)
    db.flush()

    for line in lines:
        db.add(
            JournalLine(
                journal_entry_id=entry.id,
                account_id=line['account_id'],
                debit=line.get('debit', Decimal('0')),
                credit=line.get('credit', Decimal('0')),
            )
        )
    return entry


def record_expense(db: Session, payload: ExpenseCreate, user: User) -> Expense:
    ensure_default_chart_of_accounts(db)
    expense_account = _get_account_by_code(db, ACCOUNT_CODES['operating_expense'])
    payment_account = _get_account_by_code(db, ACCOUNT_CODES['cash'] if payload.payment_method == 'cash' else ACCOUNT_CODES['bank'])

    entry = create_balanced_journal_entry(
        db,
        entry_date=payload.expense_date,
        description=payload.description or f'Expense {payload.category}',
        reference_type='expense',
        reference_id='pending',
        created_by=user.id,
        lines=[
            {'account_id': expense_account.id, 'debit': payload.amount, 'credit': Decimal('0')},
            {'account_id': payment_account.id, 'debit': Decimal('0'), 'credit': payload.amount},
        ],
    )

    expense = Expense(**payload.model_dump(), linked_journal_entry_id=entry.id, created_by=user.id)
    db.add(expense)
    db.flush()
    entry.reference_id = str(expense.id)

    db.add(
        CashTransaction(
            account_id=payment_account.id,
            transaction_type='outflow',
            reference_type='expense',
            reference_id=expense.id,
            amount=payload.amount,
        )
    )
    _audit(db, 'record_expense', 'expense', str(expense.id), user.id)
    db.commit()
    db.refresh(expense)
    return expense


def record_income(db: Session, payload: IncomeCreate, user: User) -> Income:
    ensure_default_chart_of_accounts(db)
    revenue_account = _get_account_by_code(db, ACCOUNT_CODES['revenue'])
    receipt_account = _get_account_by_code(db, ACCOUNT_CODES['cash'] if payload.payment_method == 'cash' else ACCOUNT_CODES['bank'])
    entry = create_balanced_journal_entry(
        db,
        entry_date=payload.income_date,
        description=payload.description or f'Income {payload.source}',
        reference_type='income',
        reference_id='pending',
        created_by=user.id,
        lines=[
            {'account_id': receipt_account.id, 'debit': payload.amount, 'credit': Decimal('0')},
            {'account_id': revenue_account.id, 'debit': Decimal('0'), 'credit': payload.amount},
        ],
    )
    income = Income(**payload.model_dump(), linked_journal_entry_id=entry.id)
    db.add(income)
    db.flush()
    entry.reference_id = str(income.id)
    db.add(
        CashTransaction(
            account_id=receipt_account.id,
            transaction_type='inflow',
            reference_type='income',
            reference_id=income.id,
            amount=payload.amount,
        )
    )
    _audit(db, 'record_income', 'income', str(income.id), user.id)
    db.commit()
    db.refresh(income)
    return income


def create_employee(db: Session, payload: EmployeeCreate, user: User) -> Employee:
    employee = Employee(**payload.model_dump())
    db.add(employee)
    _audit(db, 'create_employee', 'employee', 'pending', user.id)
    db.commit()
    db.refresh(employee)
    return employee


def process_payroll(db: Session, payload: PayrollCreate, user: User) -> Payroll:
    ensure_default_chart_of_accounts(db)
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail='Employee not found')

    salary_expense_account = _get_account_by_code(db, ACCOUNT_CODES['salary_expense'])
    payroll_liability_account = _get_account_by_code(db, ACCOUNT_CODES['payroll_liability'])
    base_salary = Decimal(employee.base_salary)
    bonus = Decimal(payload.bonus)
    deductions = Decimal(payload.deductions)
    net_salary = base_salary + bonus - deductions

    entry = create_balanced_journal_entry(
        db,
        entry_date=payload.period_end,
        description=f'Payroll accrual for {employee.full_name}',
        reference_type='payroll',
        reference_id='pending',
        created_by=user.id,
        lines=[
            {'account_id': salary_expense_account.id, 'debit': net_salary, 'credit': Decimal('0')},
            {'account_id': payroll_liability_account.id, 'debit': Decimal('0'), 'credit': net_salary},
        ],
    )

    payroll = Payroll(
        employee_id=payload.employee_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        base_salary=base_salary,
        bonus=bonus,
        deductions=deductions,
        net_salary=net_salary,
        linked_journal_entry_id=entry.id,
    )
    db.add(payroll)
    db.flush()
    entry.reference_id = str(payroll.id)
    _audit(db, 'process_payroll', 'payroll', str(payroll.id), user.id)
    db.commit()
    db.refresh(payroll)
    return payroll


def approve_and_pay_payroll(db: Session, payroll_id: int, otp_code: str, user: User) -> Payroll:
    if otp_code != '654321':
        raise HTTPException(status_code=403, detail='Invalid 2FA code for payroll approval')

    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail='Payroll record not found')
    if payroll.payment_status == 'paid':
        return payroll

    ensure_default_chart_of_accounts(db)
    payroll_liability_account = _get_account_by_code(db, ACCOUNT_CODES['payroll_liability'])
    cash_account = _get_account_by_code(db, ACCOUNT_CODES['cash'])

    create_balanced_journal_entry(
        db,
        entry_date=date.today(),
        description=f'Payroll settlement #{payroll.id}',
        reference_type='payroll_payment',
        reference_id=str(payroll.id),
        created_by=user.id,
        lines=[
            {'account_id': payroll_liability_account.id, 'debit': payroll.net_salary, 'credit': Decimal('0')},
            {'account_id': cash_account.id, 'debit': Decimal('0'), 'credit': payroll.net_salary},
        ],
    )
    db.add(
        CashTransaction(
            account_id=cash_account.id,
            transaction_type='outflow',
            reference_type='payroll',
            reference_id=payroll.id,
            amount=payroll.net_salary,
        )
    )
    payroll.payment_status = 'paid'
    payroll.approved_by = user.id
    payroll.approved_at = datetime.utcnow()
    _audit(db, 'approve_payroll', 'payroll', str(payroll.id), user.id)
    db.commit()
    db.refresh(payroll)
    return payroll


def generate_cashflow_report(db: Session, start_date: date, end_date: date) -> dict[str, Decimal]:
    inflows = db.query(func.coalesce(func.sum(CashTransaction.amount), 0)).filter(
        and_(
            func.date(CashTransaction.created_at) >= start_date,
            func.date(CashTransaction.created_at) <= end_date,
            CashTransaction.transaction_type == 'inflow',
            CashTransaction.reference_type.in_(['income', 'order']),
        )
    ).scalar()
    outflows = db.query(func.coalesce(func.sum(CashTransaction.amount), 0)).filter(
        and_(
            func.date(CashTransaction.created_at) >= start_date,
            func.date(CashTransaction.created_at) <= end_date,
            CashTransaction.transaction_type == 'outflow',
            CashTransaction.reference_type.in_(['expense', 'payroll']),
        )
    ).scalar()
    investing = Decimal('0')
    financing = Decimal('0')
    operating_net = Decimal(inflows) - Decimal(outflows)
    return {
        'operating_cashflow': operating_net,
        'investing_cashflow': investing,
        'financing_cashflow': financing,
        'net_cashflow': operating_net + investing + financing,
    }


def generate_profit_loss_report(db: Session, start_date: date, end_date: date) -> dict[str, Decimal]:
    code_totals = dict(
        db.query(Account.code, func.coalesce(func.sum(JournalLine.credit - JournalLine.debit), 0))
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(and_(JournalEntry.entry_date >= start_date.isoformat(), JournalEntry.entry_date <= end_date.isoformat()))
        .group_by(Account.code)
        .all()
    )
    revenue = Decimal(code_totals.get(ACCOUNT_CODES['revenue'], 0))
    cogs = Decimal('0') - Decimal(code_totals.get(ACCOUNT_CODES['cogs'], 0))
    operating_expenses = Decimal('0') - Decimal(code_totals.get(ACCOUNT_CODES['operating_expense'], 0))
    salary_expense = Decimal('0') - Decimal(code_totals.get(ACCOUNT_CODES['salary_expense'], 0))
    net_profit = revenue - cogs - operating_expenses - salary_expense
    return {
        'revenue': revenue,
        'cogs': cogs,
        'operating_expenses': operating_expenses,
        'salary_expense': salary_expense,
        'net_profit': net_profit,
    }


def generate_balance_sheet(db: Session, as_of_date: date) -> dict[str, Decimal]:
    lines = (
        db.query(Account.account_type, func.coalesce(func.sum(JournalLine.debit - JournalLine.credit), 0))
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(JournalEntry.entry_date <= as_of_date.isoformat())
        .group_by(Account.account_type)
        .all()
    )
    totals = {account_type: Decimal(amount) for account_type, amount in lines}
    assets = totals.get('asset', Decimal('0'))
    liabilities = -totals.get('liability', Decimal('0'))
    equity = -totals.get('equity', Decimal('0'))
    return {'assets': assets, 'liabilities': liabilities, 'equity': equity}


def finance_dashboard_summary(db: Session) -> dict[str, Decimal]:
    ensure_default_chart_of_accounts(db)
    today = date.today()
    month_start = today.replace(day=1)
    month_end = today

    cash_account = _get_account_by_code(db, ACCOUNT_CODES['cash'])
    bank_account = _get_account_by_code(db, ACCOUNT_CODES['bank'])
    receivable_account = _get_account_by_code(db, ACCOUNT_CODES['accounts_receivable'])
    payable_account = _get_account_by_code(db, ACCOUNT_CODES['accounts_payable'])

    def balance_for_account(account_id: int) -> Decimal:
        debit_sum, credit_sum = (
            db.query(func.coalesce(func.sum(JournalLine.debit), 0), func.coalesce(func.sum(JournalLine.credit), 0))
            .filter(JournalLine.account_id == account_id)
            .one()
        )
        return Decimal(debit_sum) - Decimal(credit_sum)

    current_cash = balance_for_account(cash_account.id) + balance_for_account(bank_account.id)
    total_receivables = balance_for_account(receivable_account.id)
    total_payables = Decimal('0') - balance_for_account(payable_account.id)

    revenue_month = Decimal(
        db.query(func.coalesce(func.sum(Income.amount), 0))
        .filter(and_(Income.income_date >= month_start, Income.income_date <= month_end))
        .scalar()
    )
    expense_month = Decimal(
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(and_(Expense.expense_date >= month_start, Expense.expense_date <= month_end))
        .scalar()
    )

    payroll_obligations = Decimal(
        db.query(func.coalesce(func.sum(Payroll.net_salary), 0))
        .filter(and_(Payroll.period_end >= today, Payroll.period_end <= today + timedelta(days=30), Payroll.payment_status != 'paid'))
        .scalar()
    )
    operating_cashflow = generate_cashflow_report(db, month_start, month_end)['operating_cashflow']
    burn_rate = expense_month

    return {
        'current_cash_balance': current_cash,
        'total_receivables': total_receivables,
        'total_payables': total_payables,
        'monthly_burn_rate': burn_rate,
        'net_operating_cashflow': operating_cashflow,
        'salary_obligations_next_30_days': payroll_obligations,
        'revenue_this_month': revenue_month,
        'expenses_this_month': expense_month,
        'net_profit_this_month': revenue_month - expense_month,
    }


def get_overdue_receivables(db: Session):
    return db.query(Invoice).filter(and_(Invoice.due_date < date.today(), Invoice.status != 'paid')).all()
