from fastapi import APIRouter
from .products import router as products_router
from .units import router as units_router
from .search import router as search_router
from .catalog import router as catalog_router
from .olx import router as olx_router

router = APIRouter()

router.include_router(products_router, prefix="/products", tags=["products"])
router.include_router(units_router, prefix="/units", tags=["units"])
router.include_router(search_router, prefix="/search", tags=["search"])
router.include_router(catalog_router, prefix="/catalog", tags=["catalog"])
router.include_router(olx_router, prefix="/olx", tags=["olx"])
