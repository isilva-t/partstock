from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

# Re-export get_db so routes can import from dependencies
def get_db_session() -> Session:
    return Depends(get_db)
