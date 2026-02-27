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


class ProductImageRead(BaseModel):
    id: int
    product_id: int
    file_name: str
    content_type: str
    s3_bucket: str
    s3_key: str
    s3_url: str

    class Config:
        from_attributes = True


class ProductImageMatchRead(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str | None
    image_url: str
    similarity_score: float

