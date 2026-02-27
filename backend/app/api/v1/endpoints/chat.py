from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.schemas.chat import WhatsAppInbound, WhatsAppOutbound

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('/webhook/inbound', response_model=WhatsAppOutbound)
def whatsapp_inbound(payload: WhatsAppInbound, db: Session = Depends(get_db)):
    inbound = Conversation(customer_phone=payload.from_phone, direction='inbound', message_text=payload.text)
    db.add(inbound)

    reply_text = f"Thanks for your message. Ref: {payload.message_id}"
    outbound = Conversation(customer_phone=payload.from_phone, direction='outbound', message_text=reply_text)
    db.add(outbound)

    db.commit()
    return WhatsAppOutbound(to_phone=payload.from_phone, text=reply_text)
