from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from database import Base


class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    # fournitures_scolaires | vetements | medicaments
    categorie = Column(String, nullable=False)
    quantite = Column(Integer, default=0)
    seuil_alerte = Column(Integer, default=10)
    unite = Column(String, default="unité")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
