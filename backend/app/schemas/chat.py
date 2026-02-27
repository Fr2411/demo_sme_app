from pydantic import BaseModel


class WhatsAppInbound(BaseModel):
    from_phone: str
    text: str
    message_id: str


class WhatsAppOutbound(BaseModel):
    to_phone: str
    text: str
