from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Beneficiaire(Base):
    __tablename__ = "beneficiaires"

    id = Column(Integer, primary_key=True, index=True)
    prenom = Column(String, nullable=False)
    nom = Column(String, nullable=False)
    # etudiant | eleve | handicape | vieux | autre
    type = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    island = Column(String, nullable=True)
    village = Column(String, nullable=True)
    foyer_id = Column(Integer, ForeignKey("foyers.id"), nullable=True)
    notes = Column(String, nullable=True)
    created_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    # Campagne pendant laquelle le bénéficiaire a été recensé (nullable).
    created_during_campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
