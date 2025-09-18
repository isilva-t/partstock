# app/models/olx.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class OLXAdvert(Base):
    __tablename__ = "olx_adverts"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    olx_advert_id = Column(String, unique=True, nullable=False)
    # limited | active | removed_by_user
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    unit = relationship("Unit", back_populates="olx_adverts")


class OLXDraftAdvert(Base):
    __tablename__ = "olx_draft_adverts"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    error = Column(Text, nullable=True)

    unit = relationship("Unit", back_populates="olx_draft_adverts")
