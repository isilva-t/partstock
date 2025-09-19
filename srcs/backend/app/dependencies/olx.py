from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.integrations.olx.service import OLXAdvertService
from app.integrations.olx.auth import OLXAuth


def get_olx_service(db: Session = Depends(get_db)) -> OLXAdvertService:
    return OLXAdvertService(db)


def get_olx_auth(db: Session = Depends(get_db)) -> OLXAuth:
    return OLXAuth(db)
