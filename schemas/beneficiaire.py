from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

TYPES_VALIDES = {"etudiant", "eleve", "handicape", "vieux", "autre"}


class BeneficiaireCreate(BaseModel):
    prenom: str
    nom: str
    type: str
    age: Optional[int] = None
    island: Optional[str] = None
    village: Optional[str] = None
    foyer_id: Optional[int] = None
    notes: Optional[str] = None


class BeneficiaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prenom: str
    nom: str
    type: str
    age: Optional[int]
    island: Optional[str]
    village: Optional[str]
    foyer_id: Optional[int]
    notes: Optional[str]
    created_during_campaign_id: Optional[int] = None
    created_at: Optional[datetime]
