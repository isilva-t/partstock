from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Unit
from app.model.olx import OLXDraftAdvert
import shutil
from pathlib import Path
from app.config import settings
from app.models import UnitPhoto

router = APIRouter()


@router.post("/{unit_id}")
def create_draft(unit_id: int, db: Session = Depends(get_db)):
    """Create OLX draft advert for a unit."""
    try:
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        if unit.status != "active":
            raise HTTPException(
                status_code=400, detail="Only active units can be advertised")

        # TODO: talk to stakeholders to see if they want duplicated adverts
        existing = db.query(OLXDraftAdvert).filter_by(
            unit_id=unit.id).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Draft already exists for this product")

        draft = OLXDraftAdvert(unit_id=unit.id)
        db.add(draft)
        db.commit()
        db.refresh(draft)

        unit_photos = db.query(UnitPhoto).filter(
            UnitPhoto.unit_id == unit.id).all()
        print(unit_photos)
        print("HERE IT IS")
        for photo in unit_photos:
            src = Path(settings.unit_PHOTO_DIR) / photo.filename
            dst = Path(settings.TEMP_PHOTO_DIR) / photo.filename
            shutil.copy2(src, dst)

        return {"id": draft.id, "unit_id": draft.unit_id, "error": draft.error}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create draft: {str(e)}")


@router.get("/")
def list_drafts(db: Session = Depends(get_db)):
    """List all OLX draft adverts."""
    try:
        drafts = db.query(OLXDraftAdvert).all()
        result = []
        for d in drafts:
            unit_reference = None
            unit_status = None

            if d.unit and d.unit.product:
                unit_reference = f"{d.unit.product.sku}-{d.unit.sku}"
                unit_status = d.unit.status

            result.append({
                "id": d.id,
                "unit_id": d.unit_id,
                "error": d.error,
                "unit_reference": unit_reference,
                "unit_status": unit_status,
            })
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch drafts: {str(e)}")


@router.delete("/{draft_id}")
def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    """Delete a draft advert (before sending)."""
    try:
        draft = db.query(OLXDraftAdvert).filter(
            OLXDraftAdvert.id == draft_id).first()
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        db.delete(draft)
        db.commit()
        return {"message": "Draft deleted", "id": draft_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete draft: {str(e)}")
