from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from database import Base


class Cotisation(Base):
    __tablename__ = "cotisations"

    id = Column(Integer, primary_key=True, index=True)
    membre_nom = Column(String, nullable=False)
    montant = Column(Float, nullable=False)
    periode_mois = Column(Integer, nullable=False)   # 1-12
    periode_annee = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
