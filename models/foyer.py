from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Foyer(Base):
    __tablename__ = "foyers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)  # FC-XXXX
    chef_prenom = Column(String, nullable=False)
    chef_nom = Column(String, nullable=False)
    island = Column(String, nullable=False)  # grande_comore | anjouan | moheli
    village = Column(String, nullable=False)
    quartier = Column(String, nullable=True)
    nb_adultes = Column(Integer, default=1)
    nb_enfants = Column(Integer, default=0)
    nb_anciens = Column(Integer, default=0)
    is_veuf = Column(Boolean, default=False)
    is_handicap = Column(Boolean, default=False)
    is_famille_nombreuse = Column(Boolean, default=False)
    is_orphelin = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    # Campagne pendant laquelle le foyer a été recensé (nullable = recensement libre ou foyer pré-existant).
    # Le foyer N'EST PAS supprimé à la clôture de la campagne, c'est juste une trace.
    created_during_campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
