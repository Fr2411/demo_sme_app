from typing import Any

from pydantic import BaseModel


class WhatsAppInbound(BaseModel):
    from_phone: str
    text: str
    message_id: str


class WhatsAppOutbound(BaseModel):
    to_phone: str
    text: str


class WhatsAppWebhookProcessResult(BaseModel):
    status: str
    processed_messages: int
    details: list[dict[str, Any]]


class WhatsAppTemplateCatalog(BaseModel):
    templates: list[dict[str, Any]]
