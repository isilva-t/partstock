from fastapi import APIRouter, Depends, Request, HTTPException, Form, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.model.user import User
from app.core.security import Security

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    uid = (request.session or {}).get("user_id")
    if not uid:
        return None
    return db.query(User).filter(User.id == uid).first()


def require_min_role(min_order: int):
    def dep(request: Request, db: Session = Depends(get_db)) -> User:
        user = get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        if user.role_order > min_order:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions")
        return user
    return dep


@router.post("/login")
def api_login(
    request: Request,
    username: str = Form(None),   # try form first
    password: str = Form(None),
    creds: dict = Body(None),     # also accept raw JSON body
    db: Session = Depends(get_db),
):
    if creds:
        username = creds.get("username", username)
        password = creds.get("password", password)

    if not username or not password:
        raise HTTPException(
            status_code=422, detail="Username and password required")

    u = Security.normalize_username(username)
    user = db.query(User).filter(User.username == u).first()
    if not user or not Security.verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    request.session["role_order"] = user.role_order
    return {"message": "login ok", "username": user.username, "role": user.role}


@router.post("/logout")
def api_logout(request: Request):
    request.session.clear()
    return {"message": "logout ok"}


@router.post("/change-password")
def api_change_password(
    request: Request,
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(40)),
):
    if not Security.verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Wrong current password")

    user.password_hash = Security.hash_password(new_password)
    db.add(user)
    db.commit()
    return {"message": "password updated"}
