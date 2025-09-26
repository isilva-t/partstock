from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Unit, UnitPhoto
from app.config import settings
import datetime
from pathlib import Path
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/photos/{filename:path}")
async def serve_unit_photo(filename: str):
    """Serve unit photo files"""
    try:
        photo_path = Path(settings.UNIT_PHOTO_DIR) / filename
        if not photo_path.exists():
            raise HTTPException(status_code=404, detail="Photo not found")
        return FileResponse(photo_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Photo not found")


@router.post("/{unit_id}/photos")
async def upload_unit_photo(
    unit_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a photo for a specific unit"""
    try:
        # Validate unit exists
        unit = db.query(Unit).filter(
            Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        # Get product for filename generation
        product = db.query(Product).filter(
            Product.id == unit.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, detail="File must be an image")

        # Count existing photos for sequence number
        existing_photos = db.query(UnitPhoto).filter(
            UnitPhoto.unit_id == unit_id
        ).count()

        if existing_photos >= 9:
            raise HTTPException(
                status_code=400, detail="Maximum 9 photos allowed per unit")

        sequence = existing_photos + 1

        # Generate filename: {unit_SKU}_{PRODUCT_SKU}_{SEQUENCE}_{TIMESTAMP}.jpg
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{unit.sku}_{product.sku}_{sequence}_{timestamp}.jpg"

        # Create unit photo directory if it doesn't exist
        photo_dir = Path(settings.UNIT_PHOTO_DIR) / product.component_ref / \
            product.sku
        photo_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = photo_dir / filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Save to database
        photo_record = UnitPhoto(
            unit_id=unit_id,
            filename=filename
        )
        db.add(photo_record)
        db.commit()
        db.refresh(photo_record)

        return {
            "id": photo_record.id,
            "filename": filename,
            "sequence": sequence,
            "unit_sku": unit.sku,
            "product_sku": product.sku
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload photo: {str(e)}"
        )


@router.get("/{unit_id}/photos")
def get_unit_photos(unit_id: int, db: Session = Depends(get_db)):
    """Get all photos for an unit"""
    try:
        unit = db.query(Unit).filter(
            Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        product = db.query(Product).filter(
            Product.id == unit.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404, detail="Product not found (GET /unit_id/photos)")

        photos = db.query(UnitPhoto).filter(
            UnitPhoto.unit_id == unit_id
        ).order_by(UnitPhoto.created_at).all()

        return [
            {
                "id": photo.id,
                "filename": product.component_ref + "/" + product.sku + "/" + photo.filename,
                "created_at": photo.created_at.strftime('%Y-%m-%d %H:%M') if photo.created_at else None
            }
            for photo in photos
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch photos: {str(e)}"
        )
