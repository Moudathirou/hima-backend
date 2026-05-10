from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from database import Base


class Distribution(Base):
    __tablename__ = "distributions"

    id = Column(Integer, primary_key=True, index=True)
    # L'un des deux doit être renseigné
    foyer_id = Column(Integer, ForeignKey("foyers.id"), nullable=True)
    beneficiaire_id = Column(Integer, ForeignKey("beneficiaires.id"), nullable=True)
    # Campagne à laquelle la distribution appartient. Nullable pour rétro-compat
    # avec les anciennes lignes (rattachées à une campagne "Historique" via migration).
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    # fournitures_scolaires | vetements | medicaments
    type = Column(String, nullable=False)
    # Item précis du quota campagne consommé (ex: "cahiers"). Optionnel.
    stock_item = Column(String, nullable=True)
    quantite = Column(Integer, default=1)
    prix = Column(Float, nullable=True)  # uniquement pour médicaments vendus
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    notes = Column(String, nullable=True)
    # Signature du bénéficiaire (base64 PNG, dataURL accepté). Trace anti-fraude.
    signature_data = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
