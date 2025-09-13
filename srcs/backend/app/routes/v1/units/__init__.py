from fastapi import APIRouter
from .crud import router as crud_router
from .photos import router as photos_router

router = APIRouter()

router.include_router(crud_router)
router.include_router(photos_router)
