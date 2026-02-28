from datetime import date
from decimal import Decimal

from backend.app.core.security import create_access_token
from backend.app.models.accounting import Account, JournalLine
from backend.app.models.client import Invoice, Payment
from backend.app.models.customer import Customer
from backend.app.models.finance import Employee, Expense, Payroll
from backend.app.models.order import Order
from backend.app.models.user import Role, User


def _auth_headers_for(client, db_session, username: str, email: str, role_name: str):
    role = db_session.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db_session.add(role)
        db_session.flush()
    user = User(username=username, email=email, password_hash='hash')
    user.roles.append(role)
    db_session.add(user)
    db_session.commit()
    token = create_access_token(username)
    return {'Authorization': f'Bearer {token}'}, user


def _setup_accounts(db_session):
    defaults = [
        ('1000', 'Cash', 'asset'),
        ('1010', 'Bank', 'asset'),
        ('1100', 'Accounts Receivable', 'asset'),
        ('2000', 'Accounts Payable', 'liability'),
        ('2100', 'Payroll Liability', 'liability'),
        ('3000', 'Owner Equity', 'equity'),
        ('3100', 'Retained Earnings', 'equity'),
        ('4000', 'Revenue', 'revenue'),
        ('5000', 'Cost of Goods Sold', 'expense'),
        ('6000', 'Operating Expenses', 'expense'),
        ('6100', 'Salary Expense', 'expense'),
    ]
    for code, name, account_type in defaults:
        if not db_session.query(Account).filter(Account.code == code).first():
            db_session.add(Account(code=code, name=name, account_type=account_type))
    db_session.commit()


def test_expense_journal_balancing(client, db_session):
    headers, _ = _auth_headers_for(client, db_session, 'fin_mgr_1', 'fin1@example.com', 'owner')
    _setup_accounts(db_session)

    response = client.post(
        '/api/v1/finance/expenses',
        json={
            'category': 'rent',
            'description': 'Office rent',
            'vendor': 'ACME Landlord',
            'amount': '1200.00',
            'payment_method': 'cash',
            'expense_date': date.today().isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 200
    expense_id = response.json()['id']

    expense = db_session.query(Expense).filter(Expense.id == expense_id).first()
    lines = db_session.query(JournalLine).filter(JournalLine.journal_entry_id == expense.linked_journal_entry_id).all()
    debit_total = sum((Decimal(line.debit) for line in lines), Decimal('0'))
    credit_total = sum((Decimal(line.credit) for line in lines), Decimal('0'))
    assert debit_total == credit_total == Decimal('1200.00')


def test_payroll_processing_accuracy(client, db_session):
    headers, _ = _auth_headers_for(client, db_session, 'fin_mgr_2', 'fin2@example.com', 'owner')
    _setup_accounts(db_session)

    employee = Employee(
        full_name='Alice Payroll',
        role_title='Engineer',
        base_salary='5000.00',
        hire_date=date(2024, 1, 1),
        employment_status='active',
        bank_account='12345',
    )
    db_session.add(employee)
    db_session.commit()

    response = client.post(
        '/api/v1/finance/payroll',
        json={
            'employee_id': employee.id,
            'period_start': '2026-01-01',
            'period_end': '2026-01-31',
            'bonus': '500.00',
            'deductions': '200.00',
        },
        headers=headers,
    )
    assert response.status_code == 200
    payroll = db_session.query(Payroll).filter(Payroll.id == response.json()['id']).first()
    assert Decimal(payroll.net_salary) == Decimal('5300.00')


def test_cashflow_calculations(client, db_session):
    headers, _ = _auth_headers_for(client, db_session, 'fin_mgr_3', 'fin3@example.com', 'owner')
    _setup_accounts(db_session)

    client.post(
        '/api/v1/finance/income',
        json={
            'source': 'sales',
            'description': 'retail sale',
            'amount': '2000.00',
            'payment_method': 'cash',
            'income_date': '2026-01-05',
        },
        headers=headers,
    )
    client.post(
        '/api/v1/finance/expenses',
        json={
            'category': 'utilities',
            'description': 'electric bill',
            'vendor': 'Power Co',
            'amount': '500.00',
            'payment_method': 'cash',
            'expense_date': '2026-01-06',
        },
        headers=headers,
    )

    today = date.today().isoformat()
    report = client.get(f'/api/v1/finance/reports/cashflow?start_date={today}&end_date={today}', headers=headers)
    assert report.status_code == 200
    assert Decimal(report.json()['net_cashflow']) == Decimal('1500.00')


def test_client_dashboard_data_integrity(client, db_session):
    headers, user = _auth_headers_for(client, db_session, 'client_user_1', 'client1@example.com', 'employee')
    customer = Customer(full_name='Client One', email=user.email, phone_e164='+19990000001')
    db_session.add(customer)
    db_session.flush()

    order = Order(
        order_number='ORD-C-001',
        customer_id=customer.id,
        status='confirmed',
        subtotal='100.00',
        tax_amount='0.00',
        discount_amount='0.00',
        total_amount='100.00',
        currency='USD',
    )
    invoice = Invoice(
        invoice_number='INV-C-001',
        customer_id=customer.id,
        order_id=None,
        issue_date=date(2026, 1, 1),
        due_date=date(2026, 1, 15),
        total_amount='100.00',
        paid_amount='40.00',
        status='open',
    )
    payment = Payment(
        customer_id=customer.id,
        invoice_id=None,
        amount='40.00',
        payment_date=date(2026, 1, 5),
        payment_method='bank_transfer',
        reference='REF123',
    )
    db_session.add_all([order, invoice, payment])
    db_session.commit()

    response = client.get('/api/v1/client/dashboard', headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload['order_history']) == 1
    assert len(payload['invoice_history']) == 1
    assert Decimal(payload['outstanding_balance']) == Decimal('60.00')


def test_rbac_financial_access_enforcement(client, db_session):
    headers_employee, _ = _auth_headers_for(client, db_session, 'employee_1', 'employee1@example.com', 'employee')
    headers_owner, _ = _auth_headers_for(client, db_session, 'owner_1', 'owner1@example.com', 'owner')

    create_response = client.post(
        '/api/v1/finance/expenses',
        json={
            'category': 'rent',
            'description': 'blocked',
            'vendor': 'Vendor',
            'amount': '100.00',
            'payment_method': 'cash',
            'expense_date': date.today().isoformat(),
        },
        headers=headers_employee,
    )
    assert create_response.status_code == 403

    read_response = client.get('/api/v1/finance/reports/pnl?start_date=2026-01-01&end_date=2026-01-31', headers=headers_employee)
    assert read_response.status_code == 403

    owner_read_response = client.get('/api/v1/finance/reports/pnl?start_date=2026-01-01&end_date=2026-01-31', headers=headers_owner)
    assert owner_read_response.status_code == 200
