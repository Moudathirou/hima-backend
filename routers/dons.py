from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.don import Don
from schemas.don import DonCreate, DonRead

router = APIRouter()


@router.post("", response_model=DonRead, status_code=201)
def create_don(data: DonCreate, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    don = Don(**data.model_dump())
    db.add(don)
    db.commit()
    db.refresh(don)
    return don


@router.get("", response_model=List[DonRead])
def list_dons(
    origine: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    q = db.query(Don)
    if origine:
        q = q.filter(Don.origine == origine)
    return q.order_by(Don.date.desc()).all()
