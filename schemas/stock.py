from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class StockCreate(BaseModel):
    nom: str
    categorie: str  # fournitures_scolaires | vetements | medicaments
    quantite: int = 0
    seuil_alerte: int = 10
    unite: str = "unité"


class StockUpdate(BaseModel):
    nom: Optional[str] = None
    quantite: Optional[int] = None
    seuil_alerte: Optional[int] = None
    unite: Optional[str] = None


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    categorie: str
    quantite: int
    seuil_alerte: int
    unite: str
    updated_at: Optional[datetime]
