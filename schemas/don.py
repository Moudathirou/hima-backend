from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DonCreate(BaseModel):
    donateur_nom: str
    montant: float
    type_don: str   # especes | nature
    origine: str    # france | comores
    description: Optional[str] = None


class DonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donateur_nom: str
    montant: float
    type_don: str
    origine: str
    description: Optional[str]
    date: Optional[datetime]
