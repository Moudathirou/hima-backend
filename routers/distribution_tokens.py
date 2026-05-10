import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.campaign import Campaign
from models.distribution_token import DistributionToken
from models.foyer import Foyer
from models.beneficiaire import Beneficiaire
from schemas.distribution_token import (
    DistributionTokenCreate,
    DistributionTokenRead,
    DistributionTokenResolved,
)

router = APIRouter()


@router.post("", response_model=DistributionTokenRead, status_code=201)
def create_token(
    data: DistributionTokenCreate,
    db: Session = Depends(get_db),
    agent=Depends(get_current_agent),
):
    # Un token ne peut être émis que dans le contexte d'une campagne active
    active_campaign = db.query(Campaign).filter(Campaign.status == "active").first()
    if not active_campaign:
        raise HTTPException(
            status_code=400,
            detail="Aucune campagne active. Impossible d'émettre un QR.",
        )

    if data.target_type == "foyer":
        target = db.query(Foyer).filter(Foyer.id == data.foyer_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Foyer introuvable")
        # Invalider les tokens précédents non consommés pour ce foyer dans cette campagne
        db.query(DistributionToken).filter(
            DistributionToken.foyer_id == data.foyer_id,
            DistributionToken.used_at.is_(None),
            DistributionToken.campaign_id == active_campaign.id,
        ).delete(synchronize_session=False)
    else:
        target = db.query(Beneficiaire).filter(Beneficiaire.id == data.beneficiaire_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Bénéficiaire introuvable")
        db.query(DistributionToken).filter(
            DistributionToken.beneficiaire_id == data.beneficiaire_id,
            DistributionToken.used_at.is_(None),
            DistributionToken.campaign_id == active_campaign.id,
        ).delete(synchronize_session=False)

    token_value = uuid.uuid4().hex
    token = DistributionToken(
        token=token_value,
        target_type=data.target_type,
        foyer_id=data.foyer_id if data.target_type == "foyer" else None,
        beneficiaire_id=data.beneficiaire_id if data.target_type == "beneficiaire" else None,
        campaign_id=active_campaign.id,
        issued_by_agent_id=agent.id,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


@router.get("/resolve/{token}", response_model=DistributionTokenResolved)
def resolve_token(token: str, db: Session = Depends(get_db), _=Depends(get_current_agent)):
    t = db.query(DistributionToken).filter(DistributionToken.token == token).first()
    if not t:
        raise HTTPException(status_code=404, detail="QR code introuvable")
    return DistributionTokenResolved(
        token=t.token,
        target_type=t.target_type,
        is_used=t.used_at is not None,
        foyer=db.query(Foyer).filter(Foyer.id == t.foyer_id).first() if t.foyer_id else None,
        beneficiaire=(
            db.query(Beneficiaire).filter(Beneficiaire.id == t.beneficiaire_id).first()
            if t.beneficiaire_id
            else None
        ),
    )
