from typing import List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


CampaignType = Literal["fournitures_scolaires", "vetements", "medicaments", "autre"]


class CampaignStockItem(BaseModel):
    item_name: str
    quantite_initiale: int = Field(ge=0)


class CampaignCreate(BaseModel):
    name: str
    type: CampaignType
    # Stock initial alloué (optionnel à la création, peut être ajouté ensuite)
    stock: List[CampaignStockItem] = []


class CampaignStockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    item_name: str
    quantite_initiale: int
    quantite_distribuee: int

    @property
    def restant(self) -> int:
        return max(self.quantite_initiale - self.quantite_distribuee, 0)


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    status: str
    created_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_by_admin_id: Optional[int]
    closed_by_admin_id: Optional[int]


class CampaignWithStock(CampaignRead):
    stock: List[CampaignStockRead] = []


class CampaignStockUpsert(BaseModel):
    """Permet à l'admin d'ajouter ou de réajuster un item de stock."""
    item_name: str
    quantite_initiale: int = Field(ge=0)
