from fastapi import FastAPI
from app.database import engine, Base
from fastapi.staticfiles import StaticFiles
from app.frontend import router as frontend_router
from app.routes.api import router as api_router
from app.routes.photos import router as photo_router
from fastapi.responses import Response

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PartStock")


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # No Content


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(frontend_router)
app.include_router(api_router)
app.include_router(photo_router)
