from decimal import Decimal

from pydantic import BaseModel


class ReturnItemIn(BaseModel):
    order_item_id: int
    quantity: Decimal
    refund_amount: Decimal


class ReturnCreate(BaseModel):
    order_id: int
    reason: str | None = None
    status: str = 'requested'
    items: list[ReturnItemIn]


class ReturnRead(BaseModel):
    id: int
    order_id: int
    status: str
    reason: str | None = None

    class Config:
        from_attributes = True
