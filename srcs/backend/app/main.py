from fastapi import FastAPI
from app.database import engine, Base
from fastapi.staticfiles import StaticFiles
from app.frontend import router as frontend_router
from app.routes.v1 import router as v1_router
from fastapi.responses import Response
from app.model.olx import OLXToken, OLXAdvert, OLXDraftAdvert
from app.model.user import User
import os
from starlette.middleware.sessions import SessionMiddleware
from app.routes.v1 import auth as auth_api
from app.routers.pages import auth_pages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PartStock")


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # No Content


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(frontend_router)
app.include_router(v1_router, prefix="/api/v1")

app.include_router(auth_api.router)
app.include_router(auth_pages.router)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-me"),
    same_site="lax",
    https_only=False,  # True if we enable HTTPS
)
