from fastapi import APIRouter
from .search import router as search_router
from .rebuild import router as rebuild_router

router = APIRouter()

router.include_router(search_router)
router.include_router(rebuild_router)
