from pydantic import BaseModel


class RapportSummary(BaseModel):
    nb_foyers: int
    nb_beneficiaires: int
    distributions_ce_mois: int
    dons_total: float
    cotisations_total: float
    nb_agents_actifs: int


class IslandStat(BaseModel):
    island: str
    nb_foyers: int
    nb_distributions: int


class DistributionStat(BaseModel):
    type: str
    total: int
