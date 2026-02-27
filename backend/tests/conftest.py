from collections.abc import Generator

import os

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.accounting import Account
from backend.app.models.customer import Customer
from backend.app.models.order import Order, OrderItem
from backend.app.models.product import Product


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        '/api/v1/auth/register',
        json={'username': 'tester', 'email': 'tester@example.com', 'password': 'password123'},
    )
    assert response.status_code == 201
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture()
def product_fixture_data(db_session: Session) -> dict[str, int]:
    customer = Customer(full_name='Fixture Customer', email='fixture@example.com', phone_e164='+10000000001')
    db_session.add(customer)
    db_session.flush()

    product = Product(
        sku='FIXTURE-SKU-1',
        name='Fixture Product',
        category='Fixture',
        description='Fixture product used in API tests',
        unit_cost='10.00',
        unit_price='15.00',
        is_active=True,
    )
    db_session.add(product)

    revenue = Account(code='4000', name='Sales', account_type='revenue')
    expense = Account(code='5000', name='COGS', account_type='expense')
    db_session.add_all([revenue, expense])

    db_session.commit()
    return {
        'product_id': product.id,
        'customer_id': customer.id,
        'revenue_account_id': revenue.id,
        'expense_account_id': expense.id,
    }


@pytest.fixture()
def order_fixture_data(db_session: Session, product_fixture_data: dict[str, int]) -> dict[str, int]:
    order = Order(
        order_number='ORD-FIX-001',
        customer_id=product_fixture_data['customer_id'],
        tax_amount='1.00',
        discount_amount='0.00',
        currency='USD',
    )
    db_session.add(order)
    db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product_fixture_data['product_id'],
        quantity='2',
        unit_price='15.00',
        line_total='30.00',
    )
    db_session.add(item)

    order.subtotal = '30.00'
    order.total_amount = '31.00'
    db_session.commit()

    return {'order_id': order.id, 'order_item_id': item.id}
