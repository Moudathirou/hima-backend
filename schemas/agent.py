from typing import Optional
from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "agent"
    island: Optional[str] = None
    village: Optional[str] = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    island: Optional[str]
    village: Optional[str]
    is_active: bool


class AgentUpdate(BaseModel):
    full_name: Optional[str] = None
    island: Optional[str] = None
    village: Optional[str] = None
    is_active: Optional[bool] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent: AgentRead
