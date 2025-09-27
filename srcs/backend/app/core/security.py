import os
import bcrypt
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.model.user import User


class Security:
    ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    DEV = 10
    CEO = 20
    MGR = 30
    OPS = 40

    ROUNDS = int(os.getenv("BCRYPT_ROUNDS"))

    @staticmethod
    def normalize_username(u: str) -> str:
        return (u or "").strip().lower()

    @staticmethod
    def hash_password(plain: str) -> str:
        salt = bcrypt.gensalt(rounds=Security.ROUNDS)
        return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def get_current_user(request: Request,
                         db: Session = Depends(get_db)
                         ) -> User | None:
        uid = (request.session or {}).get("user_id")
        if not uid:
            return None
        return db.query(User).filter(User.id == uid).first()

    @staticmethod
    def require_min_role(min_order: int):
        def dep(request: Request,
                db: Session = Depends(Security.get_db)) -> User:
            user = Security.get_current_user(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Login required")
            if user.role_order > min_order:
                raise HTTPException(
                    status_code=403, detail="Insufficient permissions")
            return user
        return dep
