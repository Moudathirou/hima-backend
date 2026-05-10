from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.auth import create_access_token, get_current_agent, require_admin
from core.security import hash_password, verify_password
from database import get_db
from models.agent import Agent
from schemas.agent import AgentCreate, AgentRead, AgentUpdate, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.username == form.username).first()
    if not agent or not verify_password(form.password, agent.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not agent.is_active:
        raise HTTPException(status_code=401, detail="Compte désactivé")

    token = create_access_token({"sub": str(agent.id)})
    return TokenResponse(access_token=token, agent=AgentRead.model_validate(agent))


@router.get("/me", response_model=AgentRead)
def me(current=Depends(get_current_agent)):
    return current


@router.post("/agents", response_model=AgentRead)
def create_agent(data: AgentCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Agent).filter(Agent.username == data.username).first():
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")
    agent = Agent(
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        island=data.island,
        village=data.village,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/agents/{agent_id}", response_model=AgentRead)
def update_agent(agent_id: int, data: AgentUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return agent
