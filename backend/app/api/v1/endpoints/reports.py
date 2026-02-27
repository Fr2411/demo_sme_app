from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.accounting import Account, JournalLine
from backend.app.models.product import Product
from backend.app.models.stock_movement import StockMovement
from backend.app.schemas.report import ProfitLossResponse, StockAgingResponse, StockAgingRow

router = APIRouter(prefix='/reports', tags=['reports'])


@router.get('/profit-loss', response_model=ProfitLossResponse)
def profit_loss(
    period_start: str = Query(...),
    period_end: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    revenue = Decimal('0')
    expense = Decimal('0')
    rows = db.query(JournalLine, Account).join(Account, JournalLine.account_id == Account.id).all()
    for line, account in rows:
        if account.account_type == 'revenue':
            revenue += Decimal(line.credit) - Decimal(line.debit)
        elif account.account_type == 'expense':
            expense += Decimal(line.debit) - Decimal(line.credit)

    return ProfitLossResponse(period_start=period_start, period_end=period_end, revenue=revenue, expense=expense, profit=revenue - expense)


@router.get('/stock-aging', response_model=StockAgingResponse)
def stock_aging(as_of_date: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows: list[StockAgingRow] = []
    for product in db.query(Product).all():
        total = Decimal('0')
        for move in db.query(StockMovement).filter(StockMovement.product_id == product.id).all():
            if move.movement_type in {'in', 'return_in'}:
                total += Decimal(move.quantity)
            elif move.movement_type in {'out', 'return_out'}:
                total -= Decimal(move.quantity)
        rows.append(StockAgingRow(product_id=product.id, sku=product.sku, qty_estimate=total))

    return StockAgingResponse(as_of_date=as_of_date, rows=rows)
