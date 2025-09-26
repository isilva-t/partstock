from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Product, Unit

router = APIRouter()


@router.get("/products")
def search_products(q: str, db: Session = Depends(get_db)):
    try:
        if not q or len(q.strip()) == 0:
            products = db.query(Product).order_by(
                Product.created_at.desc()).limit(50).all()
        else:
            # Split search terms
            terms = q.strip().split()

            if len(terms) == 1:
                # Single term search
                products = db.query(Product).filter(
                    Product.search_text.like(f"%{terms[0]}%")
                ).limit(50).all()
            else:
                # Multi-term search with position checking
                query = db.query(Product)
                for term in terms:
                    query = query.filter(Product.search_text.like(f"%{term}%"))

                # Get candidates and filter for position in Python
                products = query.limit(100).all()

                # Filter for correct position order
                filtered_products = []
                for product in products:
                    if product.search_text:
                        search_lower = product.search_text.lower()
                        positions = [search_lower.find(
                            term.lower()) for term in terms]
                        if all(pos >= 0 for pos in positions) and positions == sorted(positions):
                            filtered_products.append(product)

                products = filtered_products[:50]

        return [
            {
                "id": p.id,
                "sku": p.sku,
                "title": p.title,
                "title_ref": p.title_ref,
                "description": p.description,
                "reference_price": p.reference_price,
                "component_ref": p.component_ref
            }
            for p in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/units")
def search_units(q: str, db: Session = Depends(get_db)):
    try:
        if not q or len(q.strip()) == 0:
            units = db.query(Unit).join(Product).order_by(
                Unit.created_at.desc()).limit(50).all()
        else:
            # Split search terms
            terms = q.strip().split()

            if len(terms) == 1:
                # Single term search
                units = db.query(Unit).filter(
                    Unit.search_text.like(f"%{terms[0]}%")
                ).limit(50).all()
            else:
                # Multi-term search with position checking
                query = db.query(Unit)
                for term in terms:
                    query = query.filter(Unit.search_text.like(f"%{term}%"))

                # Get candidates and filter for position in Python
                units = query.limit(100).all()

                # Filter for correct position order
                filtered_units = []
                for unit in units:
                    if unit.search_text:
                        search_lower = unit.search_text.lower()
                        positions = [search_lower.find(
                            term.lower()) for term in terms]
                        if all(pos >= 0 for pos in positions) and positions == sorted(positions):
                            filtered_units.append(unit)

                units = filtered_units[:50]

        return [
            {
                "id": i.id,
                "sku": i.sku,
                "product_sku": i.product.sku,
                "full_reference": f"{i.product.sku} {i.sku}",
                "selling_price": i.selling_price,
                "status": i.status,
                "description": i.product.description,
                "title_suffix": i.title_suffix
            }
            for i in units
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
