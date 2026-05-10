from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator

TYPES_VALIDES = {"fournitures_scolaires", "vetements", "medicaments"}


class DistributionCreate(BaseModel):
    foyer_id: Optional[int] = None
    beneficiaire_id: Optional[int] = None
    type: str
    # Item précis du quota campagne consommé (ex: "cahiers"). Optionnel si pas de quota.
    stock_item: Optional[str] = None
    quantite: int = 1
    prix: Optional[float] = None
    notes: Optional[str] = None
    qr_token: Optional[str] = None
    # Signature du bénéficiaire (dataURL base64). Optionnel mais fortement recommandé.
    signature_data: Optional[str] = None

    @model_validator(mode="after")
    def check_destinataire(self):
        if self.foyer_id is None and self.beneficiaire_id is None:
            raise ValueError("foyer_id ou beneficiaire_id est requis")
        return self


class DistributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    foyer_id: Optional[int]
    beneficiaire_id: Optional[int]
    campaign_id: Optional[int]
    type: str
    stock_item: Optional[str]
    quantite: int
    prix: Optional[float]
    agent_id: int
    notes: Optional[str]
    signature_data: Optional[str]
    date: Optional[datetime]
