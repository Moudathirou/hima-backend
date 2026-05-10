from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.cotisation import Cotisation
from schemas.cotisation import CotisationCreate, CotisationRead

router = APIRouter()


@router.post("", response_model=CotisationRead, status_code=201)
def create_cotisation(data: CotisationCreate, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    cot = Cotisation(**data.model_dump())
    db.add(cot)
    db.commit()
    db.refresh(cot)
    return cot


@router.get("", response_model=List[CotisationRead])
def list_cotisations(
    annee: Optional[int] = Query(None),
    mois: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    q = db.query(Cotisation)
    if annee:
        q = q.filter(Cotisation.periode_annee == annee)
    if mois:
        q = q.filter(Cotisation.periode_mois == mois)
    return q.order_by(Cotisation.date.desc()).all()
