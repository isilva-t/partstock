from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Instance, ProductPhoto, InstancePhoto
from app.config import settings
import datetime
from pathlib import Path

router = APIRouter(prefix="/api", tags=["photos"])


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
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Count existing photos for sequence number
        existing_photos = db.query(ProductPhoto).filter(
            ProductPhoto.product_id == product_id
        ).count()
        
        if existing_photos >= 9:
            raise HTTPException(status_code=400, detail="Maximum 9 photos allowed per product")
        
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


@router.post("/instances/{instance_id}/photos")
async def upload_instance_photo(
    instance_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a photo for a specific instance"""
    try:
        # Validate instance exists
        instance = db.query(Instance).filter(Instance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Get product for filename generation
        product = db.query(Product).filter(Product.id == instance.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Count existing photos for sequence number
        existing_photos = db.query(InstancePhoto).filter(
            InstancePhoto.instance_id == instance_id
        ).count()
        
        if existing_photos >= 9:
            raise HTTPException(status_code=400, detail="Maximum 9 photos allowed per instance")
        
        sequence = existing_photos + 1
        
        # Generate filename: {INSTANCE_SKU}_{PRODUCT_SKU}_{SEQUENCE}_{TIMESTAMP}.jpg
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{instance.sku}_{product.sku}_{sequence}_{timestamp}.jpg"
        
        # Create instance photo directory if it doesn't exist
        photo_dir = Path(settings.INSTANCE_PHOTO_DIR)
        photo_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = photo_dir / filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Save to database
        photo_record = InstancePhoto(
            instance_id=instance_id,
            filename=filename
        )
        db.add(photo_record)
        db.commit()
        db.refresh(photo_record)
        
        return {
            "id": photo_record.id,
            "filename": filename,
            "sequence": sequence,
            "instance_sku": instance.sku,
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


@router.get("/instances/{instance_id}/photos")
def get_instance_photos(instance_id: int, db: Session = Depends(get_db)):
    """Get all photos for an instance"""
    try:
        instance = db.query(Instance).filter(Instance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        photos = db.query(InstancePhoto).filter(
            InstancePhoto.instance_id == instance_id
        ).order_by(InstancePhoto.created_at).all()
        
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
