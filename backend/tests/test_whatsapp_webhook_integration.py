from fastapi.testclient import TestClient

from backend.app.models.conversation import Conversation


def test_whatsapp_webhook_integration_processes_and_logs_messages(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr('backend.app.api.v1.endpoints.chat.whatsapp_service.validate_signature', lambda *args, **kwargs: True)
    monkeypatch.setattr(
        'backend.app.api.v1.endpoints.chat.whatsapp_service.extract_messages',
        lambda payload: [
            {
                'from_phone': '15551234567',
                'text': 'Need a discount',
                'message_id': 'wamid.integration.1',
                'profile_name': 'Integration User',
            }
        ],
    )
    monkeypatch.setattr(
        'backend.app.api.v1.endpoints.chat.whatsapp_service.route_to_orchestrator',
        lambda _message: {
            'text': 'fallback',
            'metadata': {
                'sales_agent': {'text': 'Offer 5% discount'},
                'stock_agent': {'text': 'Stock is available'},
                'discount_supervisor': {'text': 'Approved'},
            },
        },
    )

    async def fake_send_reply(*_args, **_kwargs):
        return {'status': 'sent'}

    monkeypatch.setattr('backend.app.api.v1.endpoints.chat.whatsapp_service.send_reply', fake_send_reply)

    payload = {
        'entry': [
            {
                'changes': [
                    {
                        'value': {
                            'contacts': [{'wa_id': '15551234567', 'profile': {'name': 'Integration User'}}],
                            'messages': [
                                {
                                    'id': 'wamid.integration.1',
                                    'from': '15551234567',
                                    'text': {'body': 'Need a discount'},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    response = client.post('/api/v1/chat/webhook', json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body['status'] == 'processed'
    assert body['processed_messages'] == 1
    assert body['details'][0]['send_status'] == 'sent'

    saved = db_session.query(Conversation).order_by(Conversation.id.asc()).all()
    assert len(saved) == 2
    assert saved[0].direction == 'inbound'
    assert saved[1].direction == 'outbound'
    assert saved[1].message_text == 'Offer 5% discount | Stock is available | Approved'
