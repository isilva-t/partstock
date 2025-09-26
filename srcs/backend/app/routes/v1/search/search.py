from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Unit

router = APIRouter()


@router.get("/products")
def search_products(q: str, db: Session = Depends(get_db)):
    """Search products by SKU"""
    try:
        if not q or len(q.strip()) == 0:
            products = db.query(Product).order_by(
                Product.created_at.desc()).all()
        else:

            search_term = f"%{q.strip()}%"

            products = db.query(Product).filter(
                Product.sku.like(search_term)
            ).limit(50).all()

        return [
            {
                "id": p.id,
                "sku": p.sku,
                "title": p.title,
                "title_ref": p.title_ref if p.title_ref else None,
                "description": p.description,
                "reference_price": p.reference_price,
                "component_ref": p.component_ref
            }
            for p in products
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/units")
def search_units(q: str, db: Session = Depends(get_db)):
    """Search units by SKU"""
    try:
        if not q or len(q.strip()) == 0:
            units = db.query(Unit).join(Product).order_by(
                Unit.created_at.desc()).all()
        else:
            search_term = f"%{q.strip()}%"

            units = db.query(Unit).join(Product).filter(
                Unit.sku.like(search_term)
            ).limit(50).all()

        return [
            {
                "id": i.id,
                "sku": i.sku,
                "product_sku": i.product.sku,
                "full_reference": f"{i.product.sku}-{i.sku}",
                "selling_price": i.selling_price,
                "status": i.status,
                "description": i.product.description,
                "title_suffix": i.title_suffix
            }
            for i in units
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
