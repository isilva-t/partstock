from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.olx import OLXAdvert

router = APIRouter()


@router.post("/send_all")
def send_all_adverts(db: Session = Depends(get_db)):
    """
    Placeholder: Send all draft adverts to OLX.
    Will later handle OAuth, photo upload, OLX API call.
    """
    try:
        # TODO: implement logic
        return {"message": "Send all adverts - not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send adverts: {str(e)}")


@router.get("/")
def list_adverts(db: Session = Depends(get_db)):
    """List all OLX adverts."""
    try:
        adverts = db.query(OLXAdvert).all()
        return [
            {
                "id": a.id,
                "unit_id": a.unit_id,
                "olx_advert_id": a.olx_advert_id,
                "status": a.status,
                "created_at": a.created_at,
                "valid_to": a.valid_to,
                "updated_at": a.updated_at,
            }
            for a in adverts
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch adverts: {str(e)}")


@router.post("/refresh")
def refresh_status(db: Session = Depends(get_db)):
    """
    Placeholder: Refresh OLX adverts status.
    Will later call OLX API and update DB.
    """
    try:
        # TODO: implement logic
        return {"message": "Refresh status - not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh status: {str(e)}")
