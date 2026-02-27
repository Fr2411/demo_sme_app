from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base_class import Base


class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone_e164: Mapped[str | None] = mapped_column(String(20), unique=True)
