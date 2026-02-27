from decimal import Decimal

from pydantic import BaseModel


class JournalLineIn(BaseModel):
    account_id: int
    debit: Decimal = Decimal('0')
    credit: Decimal = Decimal('0')


class JournalEntryCreate(BaseModel):
    entry_date: str
    description: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    lines: list[JournalLineIn]


class JournalEntryRead(BaseModel):
    id: int
    entry_date: str
    description: str | None = None

    class Config:
        from_attributes = True
