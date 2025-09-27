from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # store usernames lowercased in app logic; keep unique in DB
    username = Column(String(50), nullable=False, unique=True)
    role = Column(String(30), nullable=False)
    # operario|responsavel|patrao|development
    # 40|30|20|10 (lower = more power)
    role_order = Column(Integer, nullable=False)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)
