from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.auth import get_current_agent, require_admin
from database import get_db
from models.campaign import Campaign
from models.campaign_stock import CampaignStock
from models.distribution import Distribution
from models.foyer import Foyer
from models.beneficiaire import Beneficiaire
from schemas.campaign import (
    CampaignCreate,
    CampaignRead,
    CampaignWithStock,
    CampaignStockRead,
    CampaignStockUpsert,
)
from schemas.distribution import DistributionRead
from schemas.foyer import FoyerRead
from schemas.beneficiaire import BeneficiaireRead

router = APIRouter()


def _serialize_with_stock(campaign: Campaign, db: Session) -> dict:
    stocks = db.query(CampaignStock).filter(CampaignStock.campaign_id == campaign.id).all()
    base = CampaignRead.model_validate(campaign).model_dump()
    base["stock"] = [CampaignStockRead.model_validate(s).model_dump() for s in stocks]
    return base


@router.get("/active", response_model=Optional[CampaignWithStock])
def get_active_campaign(db: Session = Depends(get_db), _=Depends(get_current_agent)):
    """Renvoie la campagne en cours (status='active') ou null. Lu par l'app mobile."""
    c = db.query(Campaign).filter(Campaign.status == "active").first()
    if not c:
        return None
    return _serialize_with_stock(c, db)


@router.get("", response_model=List[CampaignRead])
def list_campaigns(
    status: Optional[str] = Query(None, description="active | closed"),
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    q = db.query(Campaign)
    if status:
        q = q.filter(Campaign.status == status)
    return q.order_by(Campaign.created_at.desc()).all()


@router.get("/{campaign_id}", response_model=CampaignWithStock)
def get_campaign(campaign_id: int, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    return _serialize_with_stock(c, db)


@router.post("", response_model=CampaignWithStock, status_code=201)
def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    # Une seule campagne active à la fois
    existing = db.query(Campaign).filter(Campaign.status == "active").first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Une campagne est déjà active (« {existing.name} »). Clôturez-la avant d'en lancer une nouvelle.",
        )

    c = Campaign(
        name=data.name,
        type=data.type,
        status="active",
        created_by_admin_id=admin.id,
    )
    db.add(c)
    db.flush()

    for s in data.stock:
        db.add(
            CampaignStock(
                campaign_id=c.id,
                item_name=s.item_name,
                quantite_initiale=s.quantite_initiale,
                quantite_distribuee=0,
            )
        )
    db.commit()
    db.refresh(c)
    return _serialize_with_stock(c, db)


@router.post("/{campaign_id}/close", response_model=CampaignRead)
def close_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    if c.status != "active":
        raise HTTPException(status_code=400, detail="Cette campagne est déjà clôturée")
    c.status = "closed"
    c.closed_at = datetime.now(timezone.utc)
    c.closed_by_admin_id = admin.id
    db.commit()
    db.refresh(c)
    return c


@router.get("/{campaign_id}/distributions", response_model=List[DistributionRead])
def list_campaign_distributions(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    return (
        db.query(Distribution)
        .filter(Distribution.campaign_id == campaign_id)
        .order_by(Distribution.date.desc())
        .all()
    )


@router.get("/{campaign_id}/stock", response_model=List[CampaignStockRead])
def list_campaign_stock(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    return db.query(CampaignStock).filter(CampaignStock.campaign_id == campaign_id).all()


@router.post("/{campaign_id}/stock", response_model=CampaignStockRead)
def upsert_campaign_stock(
    campaign_id: int,
    data: CampaignStockUpsert,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    if c.status != "active":
        raise HTTPException(status_code=400, detail="Impossible de modifier le stock d'une campagne clôturée")

    item = (
        db.query(CampaignStock)
        .filter(CampaignStock.campaign_id == campaign_id, CampaignStock.item_name == data.item_name)
        .first()
    )
    if item:
        item.quantite_initiale = data.quantite_initiale
    else:
        item = CampaignStock(
            campaign_id=campaign_id,
            item_name=data.item_name,
            quantite_initiale=data.quantite_initiale,
            quantite_distribuee=0,
        )
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{campaign_id}/foyers", response_model=List[FoyerRead])
def list_campaign_foyers(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    """Foyers recensés pendant cette campagne (pour le dashboard admin)."""
    return (
        db.query(Foyer)
        .filter(Foyer.created_during_campaign_id == campaign_id)
        .order_by(Foyer.created_at.desc())
        .all()
    )


@router.get("/{campaign_id}/beneficiaires", response_model=List[BeneficiaireRead])
def list_campaign_beneficiaires(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    return (
        db.query(Beneficiaire)
        .filter(Beneficiaire.created_during_campaign_id == campaign_id)
        .order_by(Beneficiaire.created_at.desc())
        .all()
    )
