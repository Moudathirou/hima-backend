from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint

from database import Base


class CampaignStock(Base):
    __tablename__ = "campaign_stocks"
    __table_args__ = (
        UniqueConstraint("campaign_id", "item_name", name="uq_campaign_stock_item"),
    )

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    item_name = Column(String, nullable=False)  # ex: "cahiers", "stylos", "paquets de riz"
    quantite_initiale = Column(Integer, nullable=False, default=0)
    quantite_distribuee = Column(Integer, nullable=False, default=0)
