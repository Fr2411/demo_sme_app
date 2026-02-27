from decimal import Decimal

from pydantic import BaseModel


class ProfitLossResponse(BaseModel):
    period_start: str
    period_end: str
    revenue: Decimal
    expense: Decimal
    profit: Decimal


class StockAgingRow(BaseModel):
    product_id: int
    sku: str
    qty_estimate: Decimal


class StockAgingResponse(BaseModel):
    as_of_date: str
    rows: list[StockAgingRow]
