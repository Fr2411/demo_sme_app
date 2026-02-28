from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.rbac import require_roles
from backend.app.db.session import get_db
from backend.app.models.accounting import JournalEntry, JournalLine
from backend.app.schemas.accounting import JournalEntryCreate, JournalEntryRead

router = APIRouter(prefix='/accounting', tags=['accounting'])


@router.post('/journal-entries', response_model=JournalEntryRead)
def create_journal_entry(payload: JournalEntryCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    debit_total = sum((line.debit for line in payload.lines), Decimal('0'))
    credit_total = sum((line.credit for line in payload.lines), Decimal('0'))
    if debit_total != credit_total:
        raise HTTPException(status_code=400, detail='Debit and credit totals must match')

    entry = JournalEntry(
        entry_date=payload.entry_date,
        description=payload.description,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        created_by=user.id,
    )
    db.add(entry)
    db.flush()

    for line in payload.lines:
        db.add(JournalLine(journal_entry_id=entry.id, account_id=line.account_id, debit=line.debit, credit=line.credit))

    db.commit()
    db.refresh(entry)
    return entry


@router.post('/journal-entries/{entry_id}/reverse', response_model=JournalEntryRead)
def reverse_journal_entry(entry_id: int, db: Session = Depends(get_db), user=Depends(require_roles('admin'))):
    original = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not original:
        raise HTTPException(status_code=404, detail='Journal entry not found')

    lines = db.query(JournalLine).filter(JournalLine.journal_entry_id == original.id).all()
    reversal = JournalEntry(
        entry_date=original.entry_date,
        description=f'Reversal of JE {original.id}',
        reference_type='reversal',
        reference_id=str(original.id),
        created_by=user.id,
        is_reversal=True,
        reversal_of_entry_id=original.id,
    )
    db.add(reversal)
    db.flush()
    for line in lines:
        db.add(JournalLine(journal_entry_id=reversal.id, account_id=line.account_id, debit=line.credit, credit=line.debit))

    db.commit()
    db.refresh(reversal)
    return reversal


@router.get('/journal-entries', response_model=list[JournalEntryRead])
def list_journal_entries(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(JournalEntry).order_by(JournalEntry.id.desc()).all()
