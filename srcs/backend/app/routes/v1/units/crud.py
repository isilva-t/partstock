from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Unit
from pydantic import BaseModel
from typing import Optional
from app.tools import Tools


class UnitCreateRequest(BaseModel):
    product_id: int
    year_month: str = None
    alternative_sku: Optional[str] = None
    selling_price: int
    km: Optional[int] = None  # motor kilometers
    observations: Optional[str] = None
    status: str = "active"  # active|sold|incomplete|consume
    title_suffix: Optional[str] = None


class UnitResponse(BaseModel):
    id: int
    product_id: int
    year_month: str
    sku_id: int
    sku: str
    alternative_sku: Optional[str] = None
    selling_price: int
    km: int = None
    observations: Optional[str] = None
    status: str
    product_sku: str  # parent product SKU for reference
    title_suffix: Optional[str] = None


router = APIRouter()


@router.post("/", response_model=UnitResponse)
def create_unit(unit_data: UnitCreateRequest,
                db: Session = Depends(get_db)):
    try:
        # validate product exists
        product = db.query(Product).filter(
            Product.id == unit_data.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product ID {
                                unit_data.product_id} not found")

        if unit_data.title_suffix:
            full_title = f"{product.title} {unit_data.title_suffix}"
            if len(full_title) < 16 or len(full_title) > 70:
                raise HTTPException(
                    status_code=400,
                    detail=f"Full title must be between 16 and 70 characters (got {
                        len(full_title)})"
                )

        unit_data.year_month = Tools.get_cur_year_month()
        if len(unit_data.year_month) != 3:
            raise HTTPException(
                status_code=400, detail="year_month must be 3 characters (like '25A')")

        # validate status
        # TODO: need to put that possible states on .env in future
        valid_statuses = ["active", "sold", "incomplete", "consume"]
        if unit_data.status not in valid_statuses:
            raise HTTPException(status_code=400,
                                detail=f"Status must be one of:{valid_statuses}")

        # generate next SKU ID for this year_month
        max_sku = db.query(Unit).filter(
            Unit.year_month == unit_data.year_month
        ).order_by(Unit.sku_id.desc()).first()

        next_sku_id = (max_sku.sku_id + 1) if max_sku else 1
        sku = unit_data.year_month + str(next_sku_id)

        new_unit = Unit(
            product_id=unit_data.product_id,
            year_month=unit_data.year_month,
            sku_id=next_sku_id,
            sku=sku,
            alternative_sku=unit_data.alternative_sku or "",
            selling_price=unit_data.selling_price,
            km=unit_data.km or 0,
            observations=unit_data.observations or "",
            status=unit_data.status,
            title_suffix=unit_data.title_suffix
        )

        db.add(new_unit)
        db.commit()
        db.refresh(new_unit)

        return UnitResponse(
            id=new_unit.id,
            product_id=new_unit.product_id,
            year_month=new_unit.year_month,
            sku_id=new_unit.sku_id,
            sku=new_unit.sku,
            alternative_sku=new_unit.alternative_sku,
            selling_price=new_unit.selling_price,
            km=new_unit.km,
            observations=new_unit.observations,
            status=new_unit.status,
            product_sku=product.sku,
            title_sufix=new_unit.title_suffix
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create unit: {str(e)}"
        )


@router.get("/")
def get_units(db: Session = Depends(get_db)):
    try:
        units = db.query(Unit).join(Product).all()
        # TODO: need to better document full_reference
        return [
            {
                "id": i.id,
                "sku": i.sku,
                "product_sku": i.product.sku,
                # Business display format
                "full_reference": f"{i.product.sku}-{i.sku}",
                "selling_price": i.selling_price,
                "status": i.status,
                "description": i.product.description,
                "title_suffix": i.title_suffix
            }
            for i in units
        ]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch units: {str(e)}")


@router.get("/{unit_id}")
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    try:
        unit = db.query(Unit).filter(
            Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

        product = db.query(Product).filter(
            Product.id == unit.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "id": unit.id,
            "product_id": unit.product_id,
            "sku": unit.sku,
            "product_sku": product.sku,
            "full_reference": f"{product.sku}-{unit.sku}",
            "alternative_sku": unit.alternative_sku,
            "selling_price": unit.selling_price,
            "km": unit.km,
            "observations": unit.observations,
            "status": unit.status,
            "product_description": product.description,
            "component_ref": product.component_ref,
            "created_at": unit.created_at.strftime('%Y-%m-%d %H:%M') if unit.created_at else None,
            "title_suffix": unit.title_suffix,
            "product_title": product.title,
            "has_olx_draft": len(unit.olx_draft_adverts) > 0,
            "has_olx_advert": len(unit.olx_adverts) > 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch unit: {str(e)}"
        )
