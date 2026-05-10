from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.auth import get_current_agent
from database import get_db
from models.agent import Agent
from models.beneficiaire import Beneficiaire
from models.cotisation import Cotisation
from models.distribution import Distribution
from models.don import Don
from models.foyer import Foyer
from schemas.rapports import DistributionStat, IslandStat, RapportSummary

router = APIRouter()


@router.get("/summary", response_model=RapportSummary)
def summary(db: Session = Depends(get_db), _=Depends(get_current_agent)):
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    nb_foyers = db.query(func.count(Foyer.id)).scalar() or 0
    nb_beneficiaires = db.query(func.count(Beneficiaire.id)).scalar() or 0
    distributions_ce_mois = (
        db.query(func.count(Distribution.id))
        .filter(Distribution.date >= first_of_month)
        .scalar() or 0
    )
    dons_total = db.query(func.sum(Don.montant)).scalar() or 0.0
    cotisations_total = db.query(func.sum(Cotisation.montant)).scalar() or 0.0
    nb_agents_actifs = db.query(func.count(Agent.id)).filter(Agent.is_active == True, Agent.role == "agent").scalar() or 0

    return RapportSummary(
        nb_foyers=nb_foyers,
        nb_beneficiaires=nb_beneficiaires,
        distributions_ce_mois=distributions_ce_mois,
        dons_total=float(dons_total),
        cotisations_total=float(cotisations_total),
        nb_agents_actifs=nb_agents_actifs,
    )


@router.get("/by-island", response_model=List[IslandStat])
def by_island(db: Session = Depends(get_db), _=Depends(get_current_agent)):
    islands = ["grande_comore", "anjouan", "moheli"]
    result = []
    for island in islands:
        nb_foyers = db.query(func.count(Foyer.id)).filter(Foyer.island == island).scalar() or 0
        nb_distributions = (
            db.query(func.count(Distribution.id))
            .join(Foyer, Distribution.foyer_id == Foyer.id)
            .filter(Foyer.island == island)
            .scalar() or 0
        )
        result.append(IslandStat(island=island, nb_foyers=nb_foyers, nb_distributions=nb_distributions))
    return result


@router.get("/distributions", response_model=List[DistributionStat])
def distributions_by_type(db: Session = Depends(get_db), _=Depends(get_current_agent)):
    rows = (
        db.query(Distribution.type, func.count(Distribution.id).label("total"))
        .group_by(Distribution.type)
        .all()
    )
    return [DistributionStat(type=r.type, total=r.total) for r in rows]
