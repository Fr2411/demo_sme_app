from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base_class import Base


class StockMovement(Base):
    __tablename__ = 'stock_movements'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='RESTRICT'), index=True)
    movement_type: Mapped[str] = mapped_column(
        Enum('in', 'out', 'return_in', 'return_out', 'adjustment', name='stock_movement_type'),
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    reference_type: Mapped[str | None] = mapped_column(String(50), index=True)
    reference_id: Mapped[str | None] = mapped_column(String(64), index=True)
