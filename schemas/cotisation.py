from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CotisationCreate(BaseModel):
    membre_nom: str
    montant: float
    periode_mois: int
    periode_annee: int


class CotisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    membre_nom: str
    montant: float
    periode_mois: int
    periode_annee: int
    date: datetime
