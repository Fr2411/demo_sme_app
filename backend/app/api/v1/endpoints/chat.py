from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.schemas.chat import (
    WhatsAppInbound,
    WhatsAppOutbound,
    WhatsAppTemplateCatalog,
    WhatsAppWebhookProcessResult,
)
from backend.app.services.whatsapp import WhatsAppService

router = APIRouter(prefix='/chat', tags=['chat'])
whatsapp_service = WhatsAppService()


@router.get('/webhook')
def whatsapp_webhook_verify(
    hub_mode: str = Query(alias='hub.mode'),
    hub_verify_token: str = Query(alias='hub.verify_token'),
    hub_challenge: str = Query(alias='hub.challenge'),
):
    if hub_mode != 'subscribe' or hub_verify_token != settings.whatsapp_verify_token:
        raise HTTPException(status_code=403, detail='Webhook verification failed.')
    return int(hub_challenge)


@router.post('/webhook', response_model=WhatsAppWebhookProcessResult)
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None),
):
    raw_body = await request.body()
    if settings.whatsapp_app_secret:
        is_valid = whatsapp_service.validate_signature(raw_body, x_hub_signature_256, settings.whatsapp_app_secret)
        if not is_valid:
            raise HTTPException(status_code=401, detail='Invalid webhook signature.')

    payload = await request.json()
    messages = whatsapp_service.extract_messages(payload)

    details: list[dict[str, str]] = []
    for message in messages:
        inbound = Conversation(
            customer_phone=message['from_phone'],
            direction='inbound',
            message_text=message['text'],
            channel='whatsapp',
        )
        db.add(inbound)

        orchestration_result = whatsapp_service.route_to_orchestrator(message)
        reply_text = whatsapp_service.build_reply_text(orchestration_result)
        send_status = await whatsapp_service.send_reply(to_phone=message['from_phone'], text=reply_text)

        outbound = Conversation(
            customer_phone=message['from_phone'],
            direction='outbound',
            message_text=reply_text,
            channel='whatsapp',
        )
        db.add(outbound)

        details.append(
            {
                'message_id': message['message_id'],
                'to_phone': message['from_phone'],
                'send_status': send_status['status'],
            }
        )

    db.commit()
    return WhatsAppWebhookProcessResult(status='processed', processed_messages=len(messages), details=details)


@router.post('/webhook/inbound', response_model=WhatsAppOutbound)
def whatsapp_inbound(payload: WhatsAppInbound, db: Session = Depends(get_db)):
    inbound = Conversation(customer_phone=payload.from_phone, direction='inbound', message_text=payload.text)
    db.add(inbound)

    orchestration_result = whatsapp_service.route_to_orchestrator(payload.model_dump())
    reply_text = whatsapp_service.build_reply_text(orchestration_result)

    outbound = Conversation(customer_phone=payload.from_phone, direction='outbound', message_text=reply_text)
    db.add(outbound)

    db.commit()
    return WhatsAppOutbound(to_phone=payload.from_phone, text=reply_text)


@router.get('/templates', response_model=WhatsAppTemplateCatalog)
def list_whatsapp_templates():
    return WhatsAppTemplateCatalog(templates=whatsapp_service.template_samples())
