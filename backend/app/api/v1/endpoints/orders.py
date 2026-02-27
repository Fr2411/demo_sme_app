from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.order import Order, OrderItem
from backend.app.schemas.order import OrderCreate, OrderPatch, OrderRead

router = APIRouter(prefix='/orders', tags=['orders'])


def _recompute(order: Order, db: Session) -> None:
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    subtotal = sum((item.line_total for item in items), Decimal('0'))
    order.subtotal = subtotal
    order.total_amount = subtotal + Decimal(order.tax_amount) - Decimal(order.discount_amount)


@router.post('', response_model=OrderRead)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    order = Order(
        order_number=payload.order_number,
        customer_id=payload.customer_id,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        currency=payload.currency,
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        line_total = item.quantity * item.unit_price
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total,
            )
        )

    _recompute(order, db)
    db.commit()
    db.refresh(order)
    return order


@router.get('', response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Order).order_by(Order.id.desc()).all()


@router.patch('/{order_id}', response_model=OrderRead)
def patch_order(
    order_id: int,
    payload: OrderPatch,
    x_2fa_code: str | None = Header(default=None, alias='X-2FA-Code'),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if x_2fa_code != getattr(settings, 'order_edit_2fa_code', '123456'):
        raise HTTPException(status_code=403, detail='2FA verification failed')

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(order, key, value)

    _recompute(order, db)
    db.commit()
    db.refresh(order)
    return order


@router.delete('/{order_id}', status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
    db.delete(order)
    db.commit()
    return None
