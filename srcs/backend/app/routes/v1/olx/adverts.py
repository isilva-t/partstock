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
        results = []

        for draft in drafts:

            try:
                unit = db.query(Unit).filter(Unit.id == draft.unit_id).first()
                if not unit:
                    raise HTTPException(
                        status_code=404, detail="unit not found")
                product = db.query(Product).filter(
                    Product.id == unit.product_id).first()
                if not product:
                    raise HTTPException(
                        status_code=404, detail="product not found")

                payload = service.build_advert_payload(unit, product)
                print(payload)
                result = await service.send_advert(payload)
                results.append({"draft_id": draft.id, "result": result})
                # TODO: move draft → olx_adverts
            except Exception as e:
                results.append({"draft_id": draft.id, "error": str(e)})

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
