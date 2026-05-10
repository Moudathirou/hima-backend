from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="agent")  # "admin" | "agent"
    island = Column(String, nullable=True)  # "grande_comore" | "anjouan" | "moheli"
    village = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
