from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from database import Base


class Don(Base):
    __tablename__ = "dons"

    id = Column(Integer, primary_key=True, index=True)
    donateur_nom = Column(String, nullable=False)
    montant = Column(Float, nullable=False)
    type_don = Column(String, nullable=False)   # especes | nature
    origine = Column(String, nullable=False)    # france | comores
    description = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
