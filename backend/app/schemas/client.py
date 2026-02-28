from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PaymentConfirmationCreate(BaseModel):
    invoice_id: int | None = None
    amount: Decimal
    note: str | None = None


class ReturnRequestCreate(BaseModel):
    order_id: int
    reason: str


class SupportMessageCreate(BaseModel):
    subject: str
    message: str


class ClientDashboardResponse(BaseModel):
    order_history: list[dict]
    invoice_history: list[dict]
    outstanding_balance: Decimal
    payment_history: list[dict]
    available_credit_limit: Decimal
    recent_transactions: list[dict]


class ClientStatementResponse(BaseModel):
    generated_at: datetime
    customer_id: int
    opening_balance: Decimal
    closing_balance: Decimal
    lines: list[dict]


class ClientInvoiceRead(BaseModel):
    id: int
    invoice_number: str
    issue_date: date
    due_date: date
    total_amount: Decimal
    paid_amount: Decimal
    status: str

    class Config:
        from_attributes = True
