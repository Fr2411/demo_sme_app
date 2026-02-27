from decimal import Decimal

from pydantic import BaseModel


class OrderItemIn(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal


class OrderCreate(BaseModel):
    order_number: str
    customer_id: int
    tax_amount: Decimal = Decimal('0')
    discount_amount: Decimal = Decimal('0')
    currency: str = 'USD'
    items: list[OrderItemIn]


class OrderPatch(BaseModel):
    status: str | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None


class OrderRead(BaseModel):
    id: int
    order_number: str
    customer_id: int
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str

    class Config:
        from_attributes = True
