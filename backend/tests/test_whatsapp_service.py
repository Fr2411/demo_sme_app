import hashlib
import hmac

from backend.app.services.whatsapp import WhatsAppService


def test_validate_signature_success():
    body = b'{"hello":"world"}'
    secret = 'super-secret'
    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    signature = f'sha256={digest}'

    assert WhatsAppService.validate_signature(body, signature, secret)


def test_extract_messages_returns_only_text_messages():
    payload = {
        'entry': [
            {
                'changes': [
                    {
                        'value': {
                            'contacts': [{'wa_id': '1234', 'profile': {'name': 'Alice'}}],
                            'messages': [
                                {'id': 'wamid.1', 'from': '1234', 'text': {'body': 'Hi'}},
                                {'id': 'wamid.2', 'from': '1234', 'image': {'id': 'img-id'}},
                            ],
                        }
                    }
                ]
            }
        ]
    }

    extracted = WhatsAppService.extract_messages(payload)

    assert extracted == [
        {
            'from_phone': '1234',
            'text': 'Hi',
            'message_id': 'wamid.1',
            'profile_name': 'Alice',
        }
    ]


def test_build_reply_text_prefers_agent_outputs():
    result = {
        'text': 'fallback',
        'metadata': {
            'sales_agent': {'text': 'sales'},
            'stock_agent': {'text': 'stock'},
            'discount_supervisor': {'text': 'discount'},
        },
    }

    assert WhatsAppService.build_reply_text(result) == 'sales | stock | discount'
