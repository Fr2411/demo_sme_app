from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base_class import Base


class Expense(Base):
    __tablename__ = 'expenses'
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_expenses_amount_positive'),
        Index('ix_expenses_expense_date_category', 'expense_date', 'category'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    vendor: Mapped[str | None] = mapped_column(String(150), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), index=True)
    expense_date: Mapped[date] = mapped_column(Date, index=True)
    linked_journal_entry_id: Mapped[int] = mapped_column(ForeignKey('journal_entries.id', ondelete='RESTRICT'), unique=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    linked_journal_entry = relationship('JournalEntry')


class Income(Base):
    __tablename__ = 'income'
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_income_amount_positive'),
        Index('ix_income_income_date_source', 'income_date', 'source'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), index=True)
    income_date: Mapped[date] = mapped_column(Date, index=True)
    linked_journal_entry_id: Mapped[int] = mapped_column(ForeignKey('journal_entries.id', ondelete='RESTRICT'), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    linked_journal_entry = relationship('JournalEntry')


class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    role_title: Mapped[str] = mapped_column(String(80), index=True)
    base_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, index=True)
    employment_status: Mapped[str] = mapped_column(String(30), default='active', index=True)
    bank_account: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    payroll_records = relationship('Payroll', back_populates='employee')


class Payroll(Base):
    __tablename__ = 'payroll'
    __table_args__ = (
        CheckConstraint('base_salary >= 0', name='ck_payroll_base_salary_nonnegative'),
        CheckConstraint('bonus >= 0', name='ck_payroll_bonus_nonnegative'),
        CheckConstraint('deductions >= 0', name='ck_payroll_deductions_nonnegative'),
        CheckConstraint('net_salary >= 0', name='ck_payroll_net_salary_nonnegative'),
        Index('ix_payroll_period_employee', 'period_start', 'period_end', 'employee_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id', ondelete='RESTRICT'), index=True)
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    base_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    bonus: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(
        Enum('pending', 'approved', 'paid', name='payroll_payment_status'),
        default='pending',
        index=True,
    )
    linked_journal_entry_id: Mapped[int] = mapped_column(ForeignKey('journal_entries.id', ondelete='RESTRICT'), unique=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    employee = relationship('Employee', back_populates='payroll_records')
    linked_journal_entry = relationship('JournalEntry')


class CashTransaction(Base):
    __tablename__ = 'cash_transactions'
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_cash_transactions_amount_positive'),
        Index('ix_cash_transactions_reference', 'reference_type', 'reference_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('accounts.id', ondelete='RESTRICT'), index=True)
    transaction_type: Mapped[str] = mapped_column(Enum('inflow', 'outflow', name='cash_transaction_type'), index=True)
    reference_type: Mapped[str] = mapped_column(String(40), index=True)
    reference_id: Mapped[int] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = (Index('ix_audit_logs_action_created_at', 'action', 'created_at'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
