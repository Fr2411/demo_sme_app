from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.session_log import SessionLog
from backend.app.schemas.session import SessionLogRead

router = APIRouter(prefix='/sessions', tags=['sessions'])


@router.get('/logs', response_model=list[SessionLogRead])
def list_logs(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(SessionLog).order_by(SessionLog.id.desc()).all()
