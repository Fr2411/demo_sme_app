from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import verify_password
from backend.app.db.session import get_db
from backend.app.models.product import Product
from backend.app.models.sale import Sale
from backend.app.models.user import User

router = APIRouter(tags=['ui'])


class LoginRequest(BaseModel):
    client_id: str
    username: str
    password: str


class ProductCreateRequest(BaseModel):
    client_id: str
    name: str
    category: str | None = None
    cost: float
    price: float


class SaleCreateRequest(BaseModel):
    client_id: str
    product_id: int
    qty: int
    selling_price: float


@router.post('/auth/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.client_id == payload.client_id, User.username == payload.username)
        .first()
    )
    password_ok = False
    if user:
        if user.password_hash == payload.password:
            password_ok = True
        else:
            try:
                password_ok = verify_password(payload.password, user.password_hash)
            except Exception:
                password_ok = False
    if not user or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    return {'status': 'ok', 'user': {'id': user.id, 'client_id': user.client_id, 'username': user.username, 'role': user.role}}


@router.get('/products')
def get_products(client_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.client_id == client_id).order_by(Product.id.desc()).all()
    return products


@router.post('/products', status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreateRequest, db: Session = Depends(get_db)):
    sku = f"{payload.client_id}-{payload.name.strip().lower().replace(' ', '-')}-{int(datetime.utcnow().timestamp())}"
    product = Product(
        client_id=payload.client_id,
        sku=sku,
        name=payload.name.strip(),
        category=payload.category,
        unit_cost=payload.cost,
        unit_price=payload.price,
        description='',
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get('/sales')
def get_sales(client_id: str, db: Session = Depends(get_db)):
    sales = db.query(Sale).filter(Sale.client_id == client_id).order_by(Sale.id.desc()).all()
    return sales


@router.post('/sales', status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreateRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.client_id == payload.client_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    if payload.qty <= 0:
        raise HTTPException(status_code=400, detail='Quantity should be > 0')

    sale = Sale(
        client_id=payload.client_id,
        product_id=payload.product_id,
        qty=payload.qty,
        selling_price=payload.selling_price,
        sale_date=datetime.utcnow(),
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.get('/clients')
def get_clients(db: Session = Depends(get_db)):
    rows = db.query(User.client_id).distinct().all()
    return [{'client_id': row[0]} for row in rows]

