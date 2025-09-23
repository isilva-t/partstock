from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class OLXAdvert(Base):
    __tablename__ = "olx_adverts"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    olx_advert_id = Column(String, unique=True, nullable=False)
    # limited | active | removed_by_user | pending | blocked
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


class OLXToken(Base):
    __tablename__ = "olx_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_type = Column(String(20), nullable=False,
                        unique=True)  # 'client' or 'user'
    access_token = Column(String(255), nullable=False)
    # NULL for client tokens
    refresh_token = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    scope = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
