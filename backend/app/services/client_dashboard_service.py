from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from backend.app.models.client import Invoice, Payment, PaymentConfirmation, SupportMessage
from backend.app.models.customer import Customer
from backend.app.models.order import Order
from backend.app.models.return_order import ReturnOrder
from backend.app.models.user import User


def _resolve_customer(db: Session, user: User) -> Customer:
    customer = db.query(Customer).filter(Customer.email == user.email).first()
    if not customer:
        raise HTTPException(status_code=404, detail='No customer profile linked to this user')
    return customer


def get_client_dashboard(db: Session, user: User) -> dict:
    customer = _resolve_customer(db, user)
    orders = db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.id.desc()).limit(20).all()
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer.id).order_by(Invoice.id.desc()).limit(20).all()
    payments = db.query(Payment).filter(Payment.customer_id == customer.id).order_by(Payment.id.desc()).limit(20).all()

    outstanding = sum((Decimal(inv.total_amount) - Decimal(inv.paid_amount) for inv in invoices), Decimal('0'))
    recent_transactions = [
        {
            'type': 'invoice',
            'id': inv.id,
            'date': inv.issue_date.isoformat(),
            'amount': str(inv.total_amount),
            'status': inv.status,
        }
        for inv in invoices[:5]
    ] + [
        {
            'type': 'payment',
            'id': p.id,
            'date': p.payment_date.isoformat(),
            'amount': str(p.amount),
            'method': p.payment_method,
        }
        for p in payments[:5]
    ]

    return {
        'order_history': [
            {
                'order_id': o.id,
                'order_number': o.order_number,
                'status': o.status,
                'total_amount': str(o.total_amount),
                'currency': o.currency,
            }
            for o in orders
        ],
        'invoice_history': [
            {
                'invoice_id': inv.id,
                'invoice_number': inv.invoice_number,
                'issue_date': inv.issue_date.isoformat(),
                'due_date': inv.due_date.isoformat(),
                'total_amount': str(inv.total_amount),
                'paid_amount': str(inv.paid_amount),
                'status': inv.status,
                'pdf_url': f'/api/v1/client/invoices/{inv.id}/download',
            }
            for inv in invoices
        ],
        'outstanding_balance': outstanding,
        'payment_history': [
            {
                'payment_id': p.id,
                'invoice_id': p.invoice_id,
                'amount': str(p.amount),
                'payment_date': p.payment_date.isoformat(),
                'payment_method': p.payment_method,
                'reference': p.reference,
            }
            for p in payments
        ],
        'available_credit_limit': Decimal('10000.00') - outstanding,
        'recent_transactions': recent_transactions,
    }


def list_client_orders(db: Session, user: User) -> list[dict]:
    customer = _resolve_customer(db, user)
    orders = db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.id.desc()).all()
    return [{'id': o.id, 'number': o.order_number, 'status': o.status, 'total': str(o.total_amount)} for o in orders]


def list_client_invoices(db: Session, user: User) -> list[Invoice]:
    customer = _resolve_customer(db, user)
    return db.query(Invoice).filter(Invoice.customer_id == customer.id).order_by(Invoice.id.desc()).all()


def get_client_statement(db: Session, user: User) -> dict:
    customer = _resolve_customer(db, user)
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer.id).all()
    payments = db.query(Payment).filter(Payment.customer_id == customer.id).all()

    invoice_total = sum((Decimal(i.total_amount) for i in invoices), Decimal('0'))
    payment_total = sum((Decimal(p.amount) for p in payments), Decimal('0'))
    closing = invoice_total - payment_total

    lines = [
        {'type': 'invoice', 'id': i.id, 'date': i.issue_date.isoformat(), 'debit': str(i.total_amount), 'credit': '0.00'}
        for i in invoices
    ] + [
        {'type': 'payment', 'id': p.id, 'date': p.payment_date.isoformat(), 'debit': '0.00', 'credit': str(p.amount)}
        for p in payments
    ]

    return {
        'generated_at': datetime.utcnow(),
        'customer_id': customer.id,
        'opening_balance': Decimal('0.00'),
        'closing_balance': closing,
        'lines': sorted(lines, key=lambda x: x['date']),
    }


def submit_payment_confirmation(db: Session, user: User, invoice_id: int | None, amount: Decimal, note: str | None):
    customer = _resolve_customer(db, user)
    record = PaymentConfirmation(customer_id=customer.id, invoice_id=invoice_id, amount=amount, note=note)
    db.add(record)
    db.commit()
    return {'status': 'submitted', 'confirmation_id': record.id}


def submit_return_request(db: Session, user: User, order_id: int, reason: str):
    customer = _resolve_customer(db, user)
    order = db.query(Order).filter(and_(Order.id == order_id, Order.customer_id == customer.id)).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    request = ReturnOrder(order_id=order.id, reason=reason, status='requested')
    db.add(request)
    db.commit()
    return {'status': 'submitted', 'return_request_id': request.id}


def submit_support_message(db: Session, user: User, subject: str, message: str):
    customer = _resolve_customer(db, user)
    support = SupportMessage(customer_id=customer.id, subject=subject, message=message)
    db.add(support)
    db.commit()
    return {'status': 'submitted', 'support_message_id': support.id}


def statement_pdf_stub(statement_data: dict) -> dict:
    return {
        'file_name': f"statement_{statement_data['customer_id']}.pdf",
        'content_type': 'application/pdf',
        'stub': 'PDF generation placeholder',
    }
