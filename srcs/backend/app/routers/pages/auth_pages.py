from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.routes.v1.auth import require_min_role, User

router = APIRouter(tags=["auth-pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def login_form(request: Request, error: str | None = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    # just proxy to API (internal call)
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.post("/api/v1/auth/login",
                       data={"username": username, "password": password})
    if resp.status_code != 200:
        return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout")
def logout_page(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/change-password")
def change_pw_form(request: Request, error: str | None = None, user: User = Depends(require_min_role(40))):
    return templates.TemplateResponse("change_password.html", {"request": request, "error": error})


@router.post("/change-password")
def change_pw_submit(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
):
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.post("/api/v1/auth/change-password", data={
        "current_password": current_password,
        "new_password": new_password
    })
    if resp.status_code != 200:
        return RedirectResponse(url="/change-password?error=Wrong+current+password", status_code=303)
    return RedirectResponse(url="/?msg=Password+updated", status_code=303)
