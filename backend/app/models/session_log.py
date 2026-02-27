from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base_class import Base


class SessionLog(Base):
    __tablename__ = 'session_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    details: Mapped[str | None] = mapped_column(Text)
