from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.return_order import ReturnItem, ReturnOrder
from backend.app.schemas.return_order import ReturnCreate, ReturnRead

router = APIRouter(prefix='/returns', tags=['returns'])


@router.post('', response_model=ReturnRead)
def create_return(payload: ReturnCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    ret = ReturnOrder(order_id=payload.order_id, status=payload.status, reason=payload.reason)
    db.add(ret)
    db.flush()
    for item in payload.items:
        db.add(
            ReturnItem(
                return_id=ret.id,
                order_item_id=item.order_item_id,
                quantity=item.quantity,
                refund_amount=item.refund_amount,
            )
        )
    db.commit()
    db.refresh(ret)
    return ret


@router.get('', response_model=list[ReturnRead])
def list_returns(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(ReturnOrder).order_by(ReturnOrder.id.desc()).all()
