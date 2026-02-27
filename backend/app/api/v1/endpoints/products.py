from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.product import Product
from backend.app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix='/products', tags=['products'])


@router.get('', response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.post('', response_model=ProductRead)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.query(Product).filter(Product.sku == payload.sku).first():
        raise HTTPException(status_code=409, detail='SKU already exists')
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get('/{product_id}', response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return product


@router.patch('/{product_id}', response_model=ProductRead)
def patch_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete('/{product_id}', status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    db.delete(product)
    db.commit()
    return None
