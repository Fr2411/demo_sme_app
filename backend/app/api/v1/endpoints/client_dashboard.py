from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.schemas.client import (
    ClientDashboardResponse,
    ClientInvoiceRead,
    ClientStatementResponse,
    PaymentConfirmationCreate,
    ReturnRequestCreate,
    SupportMessageCreate,
)
from backend.app.services.client_dashboard_service import (
    get_client_dashboard,
    get_client_statement,
    list_client_invoices,
    list_client_orders,
    statement_pdf_stub,
    submit_payment_confirmation,
    submit_return_request,
    submit_support_message,
)

router = APIRouter(prefix='/client', tags=['client-dashboard'])


def _require_client(user=Depends(get_current_user)):
    roles = {r.name for r in user.roles}
    if 'client' not in roles:
        raise HTTPException(status_code=403, detail='Client role required')
    return user


@router.get('/dashboard', response_model=ClientDashboardResponse)
def dashboard(db: Session = Depends(get_db), user=Depends(_require_client)):
    return get_client_dashboard(db, user)


@router.get('/orders')
def client_orders(db: Session = Depends(get_db), user=Depends(_require_client)):
    return {'orders': list_client_orders(db, user)}


@router.get('/invoices', response_model=list[ClientInvoiceRead])
def client_invoices(db: Session = Depends(get_db), user=Depends(_require_client)):
    return list_client_invoices(db, user)


@router.get('/invoices/{invoice_id}/download')
def download_invoice(invoice_id: int, db: Session = Depends(get_db), user=Depends(_require_client)):
    invoices = {inv.id: inv for inv in list_client_invoices(db, user)}
    if invoice_id not in invoices:
        raise HTTPException(status_code=404, detail='Invoice not found')
    return {
        'file_name': f"invoice_{invoices[invoice_id].invoice_number}.pdf",
        'content_type': 'application/pdf',
        'stub': 'Invoice PDF generation placeholder',
    }


@router.get('/statement', response_model=ClientStatementResponse)
def client_statement(db: Session = Depends(get_db), user=Depends(_require_client)):
    return get_client_statement(db, user)


@router.get('/statement/download')
def download_statement(db: Session = Depends(get_db), user=Depends(_require_client)):
    statement = get_client_statement(db, user)
    return statement_pdf_stub(statement)


@router.post('/payment-confirmation')
def create_payment_confirmation(payload: PaymentConfirmationCreate, db: Session = Depends(get_db), user=Depends(_require_client)):
    return submit_payment_confirmation(db, user, payload.invoice_id, payload.amount, payload.note)


@router.post('/return-request')
def create_return_request(payload: ReturnRequestCreate, db: Session = Depends(get_db), user=Depends(_require_client)):
    return submit_return_request(db, user, payload.order_id, payload.reason)


@router.post('/support-message')
def create_support_message(payload: SupportMessageCreate, db: Session = Depends(get_db), user=Depends(_require_client)):
    return submit_support_message(db, user, payload.subject, payload.message)
