from pydantic import BaseModel


class SessionLogRead(BaseModel):
    id: int
    actor: str
    action: str
    details: str | None = None

    class Config:
        from_attributes = True
