from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base_class import Base


class ReturnOrder(Base):
    __tablename__ = 'returns'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='RESTRICT'), index=True)
    status: Mapped[str] = mapped_column(String(20), default='requested', index=True)
    reason: Mapped[str | None] = mapped_column(String(255))


class ReturnItem(Base):
    __tablename__ = 'return_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    return_id: Mapped[int] = mapped_column(ForeignKey('returns.id', ondelete='CASCADE'), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey('order_items.id', ondelete='RESTRICT'), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
