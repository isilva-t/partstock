from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.olx import OLXAdvert, OLXDraftAdvert
from app.dependencies.olx import get_olx_service, get_olx_auth, OLXAdvertService
from app.models import Unit, Product

router = APIRouter()


@router.post("/send_all")
async def send_all_adverts(
    db: Session = Depends(get_db),
    olx_auth=Depends(get_olx_auth),
    service: OLXAdvertService = Depends(get_olx_service)
):
    """
    Placeholder: Send all draft adverts to OLX.
    """
    try:
        if not await olx_auth.is_token_bearer_valid():
            raise HTTPException(
                status_code=401, detail="OLX OAuth invalid or expired")

        drafts = db.query(OLXDraftAdvert).all()
        if not drafts:
            return {"message": "No draft adverts to send", }

        results = []
        successful = 0
        failed = 0

        for draft in drafts:
            result = await service.process_draft_to_olx(draft)
            results.append(result)
            if result.get("success"):
                successful += 1
            else:
                failed += 1

        return {
            "message": f"Sent {successful} adverts successfully, {failed} failed",
            "successful": successful,
            "failed": failed,
            "details": results
        }

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
