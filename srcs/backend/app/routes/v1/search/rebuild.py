from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.post("/rebuild-index")
def rebuild_search_index(db: Session = Depends(get_db)):
    try:
        # Update products search_text
        products_sql = """
        UPDATE products 
        SET search_text = title || ' ' || COALESCE(title_ref, '') || ' ' || sku,
            updated_search_at = updated_at
        WHERE updated_at != updated_search_at OR updated_search_at IS NULL
        """
        result1 = db.execute(text(products_sql))
        db.commit()

        # Update units search_text
        units_sql = """
        UPDATE units 
        SET search_text = (
            SELECT p.title || ' ' || COALESCE(p.title_ref, '') || ' ' || 
                   COALESCE(units.title_suffix, '') || ' ' || 
                   p.sku || ' ' || units.sku
            FROM products p WHERE p.id = units.product_id
        ),
        updated_search_at = updated_at
        WHERE updated_at != updated_search_at OR updated_search_at IS NULL
        """
        result2 = db.execute(text(units_sql))
        db.commit()

        return {"message": "Search index updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to rebuild index: {str(e)}")
