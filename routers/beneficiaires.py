from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.beneficiaire import Beneficiaire
from models.campaign import Campaign
from schemas.beneficiaire import BeneficiaireCreate, BeneficiaireRead

router = APIRouter()


@router.get("", response_model=List[BeneficiaireRead])
def list_beneficiaires(
    foyer_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    island: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    q = db.query(Beneficiaire)
    if foyer_id:
        q = q.filter(Beneficiaire.foyer_id == foyer_id)
    if type:
        q = q.filter(Beneficiaire.type == type)
    if island:
        q = q.filter(Beneficiaire.island == island)
    return q.order_by(Beneficiaire.created_at.desc()).all()


@router.post("", response_model=BeneficiaireRead, status_code=201)
def create_beneficiaire(data: BeneficiaireCreate, db: Session = Depends(get_db), agent=Depends(get_current_agent)):
    active_campaign = db.query(Campaign).filter(Campaign.status == "active").first()
    beneficiaire = Beneficiaire(
        **data.model_dump(),
        created_by_agent_id=agent.id,
        created_during_campaign_id=active_campaign.id if active_campaign else None,
    )
    db.add(beneficiaire)
    db.commit()
    db.refresh(beneficiaire)
    return beneficiaire


@router.get("/{beneficiaire_id}", response_model=BeneficiaireRead)
def get_beneficiaire(beneficiaire_id: int, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    b = db.query(Beneficiaire).filter(Beneficiaire.id == beneficiaire_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bénéficiaire introuvable")
    return b
