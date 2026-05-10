from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


# Types autorisés (strings stockés en clair)
TYPES_VALIDES = {"fournitures_scolaires", "vetements", "medicaments", "autre"}
STATUS_VALIDES = {"active", "closed"}


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # fournitures_scolaires | vetements | medicaments | autre
    status = Column(String, nullable=False, default="active", index=True)  # active | closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by_admin_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    closed_by_admin_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
