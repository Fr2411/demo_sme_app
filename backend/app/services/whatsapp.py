from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from ai_agents.orchestrator import AgentOrchestrator
from backend.app.core.config import settings


class WhatsAppService:
    def __init__(self, orchestrator: AgentOrchestrator | None = None) -> None:
        self.orchestrator = orchestrator or AgentOrchestrator()

    @staticmethod
    def validate_signature(raw_body: bytes, signature_header: str | None, app_secret: str) -> bool:
        if not app_secret or not signature_header:
            return False
        prefix = 'sha256='
        if not signature_header.startswith(prefix):
            return False

        expected = hmac.new(app_secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
        provided = signature_header[len(prefix) :]
        return hmac.compare_digest(expected, provided)

    @staticmethod
    def extract_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
        extracted: list[dict[str, str]] = []
        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                contacts = value.get('contacts', [])
                messages = value.get('messages', [])
                contact_map = {
                    contact.get('wa_id'): contact.get('profile', {}).get('name', '') for contact in contacts
                }
                for message in messages:
                    from_phone = message.get('from', '')
                    text = message.get('text', {}).get('body', '')
                    if not from_phone or not text:
                        continue
                    extracted.append(
                        {
                            'from_phone': from_phone,
                            'text': text,
                            'message_id': message.get('id', ''),
                            'profile_name': contact_map.get(from_phone, ''),
                        }
                    )
        return extracted

    def route_to_orchestrator(self, inbound_message: dict[str, str]) -> dict[str, Any]:
        payload = {
            'event_type': 'whatsapp_message',
            'channel': 'whatsapp',
            'customer_phone': inbound_message['from_phone'],
            'customer_name': inbound_message.get('profile_name') or 'Unknown',
            'message_text': inbound_message['text'],
            'message_id': inbound_message['message_id'],
        }
        return self.orchestrator.route(payload)

    @staticmethod
    def build_reply_text(orchestrator_result: dict[str, Any]) -> str:
        metadata = orchestrator_result.get('metadata', {})
        sales_text = metadata.get('sales_agent', {}).get('text')
        stock_text = metadata.get('stock_agent', {}).get('text')
        discount_text = metadata.get('discount_supervisor', {}).get('text')

        parts = [part for part in [sales_text, stock_text, discount_text] if part]
        if parts:
            return ' | '.join(parts)
        return orchestrator_result.get('text', 'Thanks for your message. Our team will reply shortly.')

    @staticmethod
    def template_samples() -> list[dict[str, Any]]:
        return [
            {
                'name': 'order_update_v1',
                'category': 'UTILITY',
                'language': 'en_US',
                'components': [
                    {'type': 'BODY', 'text': 'Hi {{1}}, your order {{2}} is now {{3}}.'},
                    {'type': 'FOOTER', 'text': 'Reply HELP for support.'},
                ],
            },
            {
                'name': 'cart_reminder_v1',
                'category': 'MARKETING',
                'language': 'en_US',
                'components': [
                    {'type': 'BODY', 'text': 'You still have items in your cart, {{1}}. Complete your checkout today.'},
                    {'type': 'BUTTONS', 'buttons': [{'type': 'URL', 'text': 'Checkout now', 'url': 'https://example.com/cart'}]},
                ],
            },
            {
                'name': 'support_followup_v1',
                'category': 'UTILITY',
                'language': 'en_US',
                'components': [
                    {'type': 'BODY', 'text': 'Your support ticket {{1}} has been updated: {{2}}.'},
                ],
            },
        ]

    async def send_reply(self, to_phone: str, text: str) -> dict[str, Any]:
        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            return {'status': 'skipped', 'reason': 'Missing WhatsApp API credentials.'}

        endpoint = (
            f'https://graph.facebook.com/{settings.whatsapp_api_version}/'
            f'{settings.whatsapp_phone_number_id}/messages'
        )
        payload = {
            'messaging_product': 'whatsapp',
            'to': to_phone,
            'type': 'text',
            'text': {'preview_url': False, 'body': text},
        }
        headers = {
            'Authorization': f'Bearer {settings.whatsapp_access_token}',
            'Content-Type': 'application/json',
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(endpoint, json=payload, headers=headers)

        if response.is_success:
            return {'status': 'sent', 'provider_response': response.json()}
        return {'status': 'failed', 'provider_response': response.text}
