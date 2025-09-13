from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Unit, ProductPhoto, UnitPhoto
from app.config import settings
import datetime
from pathlib import Path
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api", tags=["photos"])


@router.get("/photos/{photo_type}/{filename}")
async def serve_photo(photo_type: str, filename: str):
    """Serve photo files"""
    try:
        if photo_type == "products":
            photo_path = Path(settings.PRODUCT_PHOTO_DIR) / filename
        elif photo_type == "units":
            photo_path = Path(settings.unit_PHOTO_DIR) / filename
        else:
            raise HTTPException(status_code=404, detail="Invalid photo type")

        if not photo_path.exists():
            raise HTTPException(status_code=404, detail="Photo not found")

        return FileResponse(photo_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Photo not found")


@router.post("/products/{product_id}/photos")
async def upload_product_photo(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a photo for a specific product"""
    try:
        # Validate product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, detail="File must be an image")

        # Count existing photos for sequence number
        existing_photos = db.query(ProductPhoto).filter(
            ProductPhoto.product_id == product_id
        ).count()

        if existing_photos >= 9:
            raise HTTPException(
                status_code=400, detail="Maximum 9 photos allowed per product")

        sequence = existing_photos + 1

        # Generate filename: {PRODUCT_SKU}_{SEQUENCE}_{TIMESTAMP}.jpg
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{product.sku}_{sequence}_{timestamp}.jpg"

        # Create product photo directory if it doesn't exist
        photo_dir = Path(settings.PRODUCT_PHOTO_DIR)
        photo_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = photo_dir / filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Save to database
        photo_record = ProductPhoto(
            product_id=product_id,
            filename=filename
        )
        db.add(photo_record)
        db.commit()
        db.refresh(photo_record)

        return {
            "id": photo_record.id,
            "filename": filename,
            "sequence": sequence,
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


@router.post("/units/{unit_id}/photos")
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
        photo_dir = Path(settings.unit_PHOTO_DIR)
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


@router.get("/products/{product_id}/photos")
def get_product_photos(product_id: int, db: Session = Depends(get_db)):
    """Get all photos for a product"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        photos = db.query(ProductPhoto).filter(
            ProductPhoto.product_id == product_id
        ).order_by(ProductPhoto.created_at).all()

        return [
            {
                "id": photo.id,
                "filename": photo.filename,
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


@router.get("/units/{unit_id}/photos")
def get_unit_photos(unit_id: int, db: Session = Depends(get_db)):
    """Get all photos for an unit"""
    try:
        unit = db.query(Unit).filter(
            Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        photos = db.query(UnitPhoto).filter(
            UnitPhoto.unit_id == unit_id
        ).order_by(UnitPhoto.created_at).all()

        return [
            {
                "id": photo.id,
                "filename": photo.filename,
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
