from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.integrations.olx.service import OLXAdvertService

def get_olx_service(db: Session = Depends(get_db)) -> OLXAdvertService:
    return OLXAdvertService(db)
