from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


class FoyerCreate(BaseModel):
    chef_prenom: str
    chef_nom: str
    island: str
    village: str
    quartier: Optional[str] = None
    nb_adultes: int = 1
    nb_enfants: int = 0
    nb_anciens: int = 0
    is_veuf: bool = False
    is_handicap: bool = False
    is_famille_nombreuse: bool = False
    is_orphelin: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FoyerUpdate(BaseModel):
    chef_prenom: Optional[str] = None
    chef_nom: Optional[str] = None
    island: Optional[str] = None
    village: Optional[str] = None
    quartier: Optional[str] = None
    nb_adultes: Optional[int] = None
    nb_enfants: Optional[int] = None
    nb_anciens: Optional[int] = None
    is_veuf: Optional[bool] = None
    is_handicap: Optional[bool] = None
    is_famille_nombreuse: Optional[bool] = None
    is_orphelin: Optional[bool] = None


class FoyerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    chef_prenom: str
    chef_nom: str
    island: str
    village: str
    quartier: Optional[str]
    nb_adultes: int
    nb_enfants: int
    nb_anciens: int
    is_veuf: bool
    is_handicap: bool
    is_famille_nombreuse: bool
    is_orphelin: bool
    latitude: Optional[float]
    longitude: Optional[float]
    created_by_agent_id: Optional[int]
    created_during_campaign_id: Optional[int] = None
    created_at: Optional[datetime]

    @property
    def total_membres(self) -> int:
        return self.nb_adultes + self.nb_enfants + self.nb_anciens
