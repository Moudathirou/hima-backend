from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


class DistributionToken(Base):
    __tablename__ = "distribution_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    # 'foyer' | 'beneficiaire'
    target_type = Column(String, nullable=False)
    # Campagne dans laquelle le token a été émis. Nullable (anciennes lignes).
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    foyer_id = Column(Integer, ForeignKey("foyers.id"), nullable=True)
    beneficiaire_id = Column(Integer, ForeignKey("beneficiaires.id"), nullable=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    issued_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    used_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    distribution_id = Column(Integer, ForeignKey("distributions.id"), nullable=True)
