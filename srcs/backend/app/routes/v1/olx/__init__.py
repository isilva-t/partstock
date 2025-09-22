from fastapi import APIRouter
from .drafts import router as drafts_router
from .adverts import router as adverts_router
from .auth import router as auth_router

router = APIRouter()
router.include_router(drafts_router, prefix="/drafts", tags=["olx-drafts"])
router.include_router(adverts_router, prefix="/adverts", tags=["olx-adverts"])
router.include_router(auth_router, tags=["olx-auth"])


@router.get("/ping")
def ping():
    return {"message": "OLX router is alive"}
