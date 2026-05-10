from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator

from schemas.foyer import FoyerRead
from schemas.beneficiaire import BeneficiaireRead


class DistributionTokenCreate(BaseModel):
    target_type: Literal["foyer", "beneficiaire"]
    foyer_id: Optional[int] = None
    beneficiaire_id: Optional[int] = None

    @model_validator(mode="after")
    def check_target(self):
        if self.target_type == "foyer" and self.foyer_id is None:
            raise ValueError("foyer_id est requis quand target_type='foyer'")
        if self.target_type == "beneficiaire" and self.beneficiaire_id is None:
            raise ValueError("beneficiaire_id est requis quand target_type='beneficiaire'")
        return self


class DistributionTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    target_type: str
    foyer_id: Optional[int]
    beneficiaire_id: Optional[int]
    issued_at: Optional[datetime]
    used_at: Optional[datetime]


class DistributionTokenResolved(BaseModel):
    token: str
    target_type: str
    is_used: bool
    foyer: Optional[FoyerRead] = None
    beneficiaire: Optional[BeneficiaireRead] = None
