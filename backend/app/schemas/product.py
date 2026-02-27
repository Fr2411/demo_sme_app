from decimal import Decimal

from pydantic import BaseModel


class ProductBase(BaseModel):
    sku: str
    name: str
    category: str | None = None
    description: str | None = None
    unit_cost: Decimal
    unit_price: Decimal
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    is_active: bool | None = None


class ProductRead(ProductBase):
    id: int

    class Config:
        from_attributes = True
