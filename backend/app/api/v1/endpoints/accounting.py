from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.accounting import JournalEntry, JournalLine
from backend.app.schemas.accounting import JournalEntryCreate, JournalEntryRead

router = APIRouter(prefix='/accounting', tags=['accounting'])


@router.post('/journal-entries', response_model=JournalEntryRead)
def create_journal_entry(payload: JournalEntryCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    debit_total = sum((line.debit for line in payload.lines), Decimal('0'))
    credit_total = sum((line.credit for line in payload.lines), Decimal('0'))
    if debit_total != credit_total:
        raise HTTPException(status_code=400, detail='Debit and credit totals must match')

    entry = JournalEntry(
        entry_date=payload.entry_date,
        description=payload.description,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
    )
    db.add(entry)
    db.flush()

    for line in payload.lines:
        db.add(JournalLine(journal_entry_id=entry.id, account_id=line.account_id, debit=line.debit, credit=line.credit))

    db.commit()
    db.refresh(entry)
    return entry


@router.get('/journal-entries', response_model=list[JournalEntryRead])
def list_journal_entries(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(JournalEntry).order_by(JournalEntry.id.desc()).all()
