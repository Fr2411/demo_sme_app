from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base_class import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_phone: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(10), index=True)
    message_text: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(20), default='whatsapp')
