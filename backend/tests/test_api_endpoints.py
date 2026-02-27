from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_healthcheck(client: TestClient):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_auth_login(client: TestClient):
    client.post('/api/v1/auth/register', json={'username': 'login-user', 'email': 'login@example.com', 'password': 'secure123'})
    response = client.post('/api/v1/auth/login', json={'username': 'login-user', 'password': 'secure123'})
    assert response.status_code == 200
    assert 'access_token' in response.json()


def test_products_endpoints(client: TestClient, auth_headers: dict[str, str], monkeypatch):
    create_response = client.post(
        '/api/v1/products',
        headers=auth_headers,
        json={
            'sku': 'SKU-TEST-1',
            'name': 'Test Product',
            'category': 'Test',
            'description': 'API test product',
            'unit_cost': '9.00',
            'unit_price': '11.00',
            'is_active': True,
        },
    )
    assert create_response.status_code == 200
    product_id = create_response.json()['id']

    list_response = client.get('/api/v1/products', headers=auth_headers)
    assert list_response.status_code == 200
    assert any(row['id'] == product_id for row in list_response.json())

    get_response = client.get(f'/api/v1/products/{product_id}', headers=auth_headers)
    assert get_response.status_code == 200

    patch_response = client.patch(
        f'/api/v1/products/{product_id}',
        headers=auth_headers,
        json={'name': 'Updated Product'},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()['name'] == 'Updated Product'

    class FakeStorage:
        def upload_product_image(self, **_kwargs):
            return SimpleNamespace(bucket='bucket', key='path/image.png', url='https://example.com/image.png')

    class FakeEmbeddings:
        def create_embedding(self, **_kwargs):
            return [0.01] * 1536

    class FakeMatcher:
        def find_top_matches(self, db, query_embedding, top_k):
            assert len(query_embedding) == 1536
            assert top_k == 2
            return [
                {
                    'product_id': product_id,
                    'sku': 'SKU-TEST-1',
                    'name': 'Updated Product',
                    'category': 'Test',
                    'image_url': 'https://example.com/image.png',
                    'similarity_score': 0.98,
                }
            ]

    monkeypatch.setattr('backend.app.api.v1.endpoints.products.S3ImageStorageService', FakeStorage)
    monkeypatch.setattr('backend.app.api.v1.endpoints.products.OpenAIImageEmbeddingService', FakeEmbeddings)
    monkeypatch.setattr('backend.app.api.v1.endpoints.products.ImageMatchingService', FakeMatcher)

    upload_response = client.post(
        f'/api/v1/products/{product_id}/images',
        headers=auth_headers,
        files={'image': ('product.png', b'fake-image-bytes', 'image/png')},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()['product_id'] == product_id

    search_response = client.post(
        '/api/v1/products/image-search',
        headers=auth_headers,
        files={'screenshot': ('screen.png', b'img', 'image/png')},
        data={'top_k': 2},
    )
    assert search_response.status_code == 200
    assert search_response.json()[0]['product_id'] == product_id

    delete_response = client.delete(f'/api/v1/products/{product_id}', headers=auth_headers)
    assert delete_response.status_code == 204


def test_inventory_endpoints(
    client: TestClient,
    auth_headers: dict[str, str],
    product_fixture_data: dict[str, int],
):
    create_response = client.post(
        '/api/v1/inventory/adjustments',
        headers=auth_headers,
        json={
            'product_id': product_fixture_data['product_id'],
            'movement_type': 'in',
            'quantity': '3',
            'reason': 'restock',
            'reference_type': 'purchase',
            'reference_id': 'PO-1',
        },
    )
    assert create_response.status_code == 200

    list_response = client.get('/api/v1/inventory/movements', headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_orders_endpoints(client: TestClient, auth_headers: dict[str, str], product_fixture_data: dict[str, int]):
    create_response = client.post(
        '/api/v1/orders',
        headers=auth_headers,
        json={
            'order_number': 'ORD-API-1',
            'customer_id': product_fixture_data['customer_id'],
            'tax_amount': '2.00',
            'discount_amount': '1.00',
            'currency': 'USD',
            'items': [
                {
                    'product_id': product_fixture_data['product_id'],
                    'quantity': '2',
                    'unit_price': '15.00',
                }
            ],
        },
    )
    assert create_response.status_code == 200
    order_id = create_response.json()['id']

    list_response = client.get('/api/v1/orders', headers=auth_headers)
    assert list_response.status_code == 200
    assert any(row['id'] == order_id for row in list_response.json())

    patch_response = client.patch(
        f'/api/v1/orders/{order_id}',
        headers={**auth_headers, 'X-2FA-Code': '123456'},
        json={'status': 'confirmed'},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()['status'] == 'confirmed'

    delete_response = client.delete(f'/api/v1/orders/{order_id}', headers=auth_headers)
    assert delete_response.status_code == 204


def test_returns_endpoints(
    client: TestClient,
    auth_headers: dict[str, str],
    order_fixture_data: dict[str, int],
):
    create_response = client.post(
        '/api/v1/returns',
        headers=auth_headers,
        json={
            'order_id': order_fixture_data['order_id'],
            'status': 'requested',
            'reason': 'Damaged item',
            'items': [
                {
                    'order_item_id': order_fixture_data['order_item_id'],
                    'quantity': '1',
                    'refund_amount': '15.00',
                }
            ],
        },
    )
    assert create_response.status_code == 200

    list_response = client.get('/api/v1/returns', headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_accounting_and_reports_endpoints(
    client: TestClient,
    auth_headers: dict[str, str],
    product_fixture_data: dict[str, int],
):
    create_response = client.post(
        '/api/v1/accounting/journal-entries',
        headers=auth_headers,
        json={
            'entry_date': '2026-01-01',
            'description': 'Sale booked',
            'reference_type': 'order',
            'reference_id': 'ORD-1',
            'lines': [
                {'account_id': product_fixture_data['expense_account_id'], 'debit': '25.00', 'credit': '0.00'},
                {'account_id': product_fixture_data['revenue_account_id'], 'debit': '0.00', 'credit': '25.00'},
            ],
        },
    )
    assert create_response.status_code == 200

    list_response = client.get('/api/v1/accounting/journal-entries', headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    profit_loss_response = client.get(
        '/api/v1/reports/profit-loss?period_start=2026-01-01&period_end=2026-01-31',
        headers=auth_headers,
    )
    assert profit_loss_response.status_code == 200
    assert profit_loss_response.json()['profit'] == '0.00'

    stock_aging_response = client.get('/api/v1/reports/stock-aging?as_of_date=2026-01-31', headers=auth_headers)
    assert stock_aging_response.status_code == 200
    assert stock_aging_response.json()['as_of_date'] == '2026-01-31'


def test_chat_templates_and_inbound(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        'backend.app.api.v1.endpoints.chat.whatsapp_service.route_to_orchestrator',
        lambda _message: {'text': 'Thanks for reaching out', 'metadata': {}},
    )
    templates_response = client.get('/api/v1/chat/templates')
    assert templates_response.status_code == 200
    assert len(templates_response.json()['templates']) > 0

    inbound_response = client.post(
        '/api/v1/chat/webhook/inbound',
        json={'from_phone': '+15551234567', 'text': 'Any offers?', 'message_id': 'wamid.manual.1'},
    )
    assert inbound_response.status_code == 200
    assert inbound_response.json()['to_phone'] == '+15551234567'


def test_webhook_verify_and_sessions_logs(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session,
):
    verify_response = client.get(
        '/api/v1/chat/webhook?hub.mode=subscribe&hub.verify_token=change_me_verify_token&hub.challenge=123',
    )
    assert verify_response.status_code == 200
    assert verify_response.json() == 123

    from backend.app.models.session_log import SessionLog

    db_session.add(SessionLog(actor='tester', action='login', details='fixture log'))
    db_session.commit()

    logs_response = client.get('/api/v1/sessions/logs', headers=auth_headers)
    assert logs_response.status_code == 200
    assert logs_response.json()[0]['actor'] == 'tester'
