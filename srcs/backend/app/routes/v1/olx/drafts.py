from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Unit
from app.model.olx import OLXDraftAdvert

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

        draft = OLXDraftAdvert(unit_id=unit.id)
        db.add(draft)
        db.commit()
        db.refresh(draft)

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
        return [{"id": d.id, "unit_id": d.unit_id, "error": d.error} for d in drafts]
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
