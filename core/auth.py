from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_agent(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from models.agent import Agent

    payload = decode_token(token)
    agent_id: Optional[int] = payload.get("sub")
    if agent_id is None:
        raise HTTPException(status_code=401, detail="Token invalide")

    agent = db.query(Agent).filter(Agent.id == int(agent_id)).first()
    if not agent or not agent.is_active:
        raise HTTPException(status_code=401, detail="Compte désactivé ou introuvable")
    return agent


async def require_admin(agent=Depends(get_current_agent)):
    if agent.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    return agent
