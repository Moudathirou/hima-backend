from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.campaign import Campaign
from models.campaign_stock import CampaignStock
from models.distribution import Distribution
from models.distribution_token import DistributionToken
from schemas.distribution import DistributionCreate, DistributionRead
from services.stock_service import decrement_stock

router = APIRouter()


def _get_active_campaign(db: Session) -> Optional[Campaign]:
    return db.query(Campaign).filter(Campaign.status == "active").first()


def _decrement_campaign_quota(db: Session, campaign_id: int, item_name: Optional[str], quantite: int) -> None:
    """Décrémente le quota campagne pour l'item donné. Bloque si insuffisant.
    Si aucun stock n'est défini pour la campagne, on autorise (pas de quota = pas de contrôle)."""
    items = db.query(CampaignStock).filter(CampaignStock.campaign_id == campaign_id).all()
    if not items:
        return  # campagne sans quota défini

    if not item_name:
        raise HTTPException(
            status_code=400,
            detail="Cette campagne a un quota défini : précisez 'stock_item' (ex: 'cahiers').",
        )

    target = next((s for s in items if s.item_name == item_name), None)
    if not target:
        raise HTTPException(
            status_code=400,
            detail=f"L'item '{item_name}' n'existe pas dans le quota de cette campagne.",
        )
    restant = target.quantite_initiale - target.quantite_distribuee
    if restant < quantite:
        raise HTTPException(
            status_code=400,
            detail=f"Quota épuisé pour '{item_name}' : reste {max(restant, 0)} sur le stock allouée à cette campagne.",
        )
    target.quantite_distribuee += quantite
    db.flush()


@router.post("", response_model=DistributionRead, status_code=201)
def create_distribution(data: DistributionCreate, db: Session = Depends(get_db), agent=Depends(get_current_agent)):
    # 1. Une campagne active est obligatoire
    campaign = _get_active_campaign(db)
    if not campaign:
        raise HTTPException(
            status_code=400,
            detail="Aucune campagne active. Demandez à un administrateur d'en lancer une.",
        )

    # 2. Vérifier le QR si fourni
    token_obj: Optional[DistributionToken] = None
    if data.qr_token:
        token_obj = db.query(DistributionToken).filter(DistributionToken.token == data.qr_token).first()
        if not token_obj:
            raise HTTPException(status_code=404, detail="QR code introuvable")
        if token_obj.used_at is not None:
            raise HTTPException(status_code=409, detail="Ce QR code a déjà été utilisé")
        # QR doit appartenir à la campagne en cours (anti-magouille : pas de réutilisation entre campagnes)
        if token_obj.campaign_id is not None and token_obj.campaign_id != campaign.id:
            raise HTTPException(status_code=409, detail="Ce QR a été émis pour une autre campagne")
        if token_obj.target_type == "foyer" and token_obj.foyer_id != data.foyer_id:
            raise HTTPException(status_code=400, detail="QR code ne correspond pas à ce foyer")
        if token_obj.target_type == "beneficiaire" and token_obj.beneficiaire_id != data.beneficiaire_id:
            raise HTTPException(status_code=400, detail="QR code ne correspond pas à ce bénéficiaire")

    # 3. Unicité : un foyer/bénéficiaire ne peut recevoir qu'une fois par campagne
    dup_q = db.query(Distribution).filter(Distribution.campaign_id == campaign.id)
    if data.foyer_id:
        if dup_q.filter(Distribution.foyer_id == data.foyer_id).first():
            raise HTTPException(status_code=409, detail="Ce foyer a déjà reçu une distribution dans cette campagne")
    if data.beneficiaire_id:
        if dup_q.filter(Distribution.beneficiaire_id == data.beneficiaire_id).first():
            raise HTTPException(status_code=409, detail="Ce bénéficiaire a déjà reçu une distribution dans cette campagne")

    # 4. Décrémenter le quota campagne (anti-fraude principal)
    _decrement_campaign_quota(db, campaign.id, data.stock_item, data.quantite)

    # 5. Décrémenter aussi le stock global existant (rétro-compat)
    try:
        decrement_stock(db, data.type, data.quantite)
    except HTTPException:
        # Si pas de stock global configuré, on continue (le quota campagne fait foi)
        pass

    # 6. Créer la distribution
    payload = data.model_dump(exclude={"qr_token"})
    dist = Distribution(**payload, campaign_id=campaign.id, agent_id=agent.id)
    db.add(dist)
    db.flush()

    if token_obj is not None:
        token_obj.used_at = datetime.now(timezone.utc)
        token_obj.used_by_agent_id = agent.id
        token_obj.distribution_id = dist.id

    db.commit()
    db.refresh(dist)
    return dist


@router.get("", response_model=List[DistributionRead])
def list_distributions(
    foyer_id: Optional[int] = Query(None),
    beneficiaire_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    campaign_id: Optional[int] = Query(None, description="Filtrer par campagne. Par défaut : campagne active."),
    all_campaigns: bool = Query(False, description="Si true, ne filtre pas par campagne"),
    db: Session = Depends(get_db),
    _=Depends(get_current_agent),
):
    q = db.query(Distribution)

    if not all_campaigns:
        if campaign_id is None:
            active = _get_active_campaign(db)
            if active:
                q = q.filter(Distribution.campaign_id == active.id)
            else:
                # Pas de campagne active : renvoyer une liste vide pour le mobile
                return []
        else:
            q = q.filter(Distribution.campaign_id == campaign_id)

    if foyer_id:
        q = q.filter(Distribution.foyer_id == foyer_id)
    if beneficiaire_id:
        q = q.filter(Distribution.beneficiaire_id == beneficiaire_id)
    if type:
        q = q.filter(Distribution.type == type)
    return q.order_by(Distribution.date.desc()).all()
