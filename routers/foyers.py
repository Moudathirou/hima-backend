from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.campaign import Campaign
from models.foyer import Foyer
from schemas.foyer import FoyerCreate, FoyerRead, FoyerUpdate
from services.foyer_service import generate_fc_code

router = APIRouter()


@router.get("", response_model=List[FoyerRead])
def list_foyers(
    island: Optional[str] = Query(None),
    village: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    q = db.query(Foyer)
    if island:
        q = q.filter(Foyer.island == island)
    if village:
        q = q.filter(Foyer.village.ilike(f"%{village}%"))
    if search:
        q = q.filter(
            Foyer.chef_nom.ilike(f"%{search}%")
            | Foyer.chef_prenom.ilike(f"%{search}%")
            | Foyer.code.ilike(f"%{search}%")
        )
    return q.order_by(Foyer.created_at.desc()).all()


@router.post("", response_model=FoyerRead, status_code=201)
def create_foyer(data: FoyerCreate, db: Session = Depends(get_db), agent=Depends(get_current_agent)):
    code = generate_fc_code(db)
    # Si une campagne est active, on trace que ce foyer y a été recensé.
    # Le foyer reste persistant après clôture (juste une trace d'origine).
    active_campaign = db.query(Campaign).filter(Campaign.status == "active").first()
    foyer = Foyer(
        **data.model_dump(),
        code=code,
        created_by_agent_id=agent.id,
        created_during_campaign_id=active_campaign.id if active_campaign else None,
    )
    db.add(foyer)
    db.commit()
    db.refresh(foyer)
    return foyer


@router.get("/by-code/{code}", response_model=FoyerRead)
def get_foyer_by_code(code: str, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    foyer = db.query(Foyer).filter(Foyer.code == code.upper()).first()
    if not foyer:
        raise HTTPException(status_code=404, detail=f"Foyer '{code}' introuvable")
    return foyer


@router.get("/{foyer_id}", response_model=FoyerRead)
def get_foyer(foyer_id: int, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    foyer = db.query(Foyer).filter(Foyer.id == foyer_id).first()
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable")
    return foyer


@router.put("/{foyer_id}", response_model=FoyerRead)
def update_foyer(foyer_id: int, data: FoyerUpdate, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    foyer = db.query(Foyer).filter(Foyer.id == foyer_id).first()
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(foyer, field, value)
    db.commit()
    db.refresh(foyer)
    return foyer
