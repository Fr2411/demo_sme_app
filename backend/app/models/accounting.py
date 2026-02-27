from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base_class import Base


class Account(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    account_type: Mapped[str] = mapped_column(String(20), index=True)


class JournalEntry(Base):
    __tablename__ = 'journal_entries'

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_date: Mapped[str] = mapped_column(String(10), index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    reference_type: Mapped[str | None] = mapped_column(String(60), index=True)
    reference_id: Mapped[str | None] = mapped_column(String(64), index=True)


class JournalLine(Base):
    __tablename__ = 'journal_lines'

    id: Mapped[int] = mapped_column(primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey('journal_entries.id', ondelete='CASCADE'), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey('accounts.id', ondelete='RESTRICT'), index=True)
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
