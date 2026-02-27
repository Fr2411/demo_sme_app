from decimal import Decimal

from pydantic import BaseModel


class InventoryAdjustmentRequest(BaseModel):
    product_id: int
    movement_type: str
    quantity: Decimal
    reason: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None


class StockMovementRead(InventoryAdjustmentRequest):
    id: int

    class Config:
        from_attributes = True
