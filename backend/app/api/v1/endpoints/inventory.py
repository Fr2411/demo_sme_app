from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.product import Product
from backend.app.models.stock_movement import StockMovement
from backend.app.schemas.inventory import InventoryAdjustmentRequest, StockMovementRead

router = APIRouter(prefix='/inventory', tags=['inventory'])


@router.post('/adjustments', response_model=StockMovementRead)
def create_adjustment(payload: InventoryAdjustmentRequest, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    movement = StockMovement(**payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get('/movements', response_model=list[StockMovementRead])
def list_movements(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(StockMovement).order_by(StockMovement.id.desc()).all()
