from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Make, Model
from app.models import Category, SubCategory, Component
from app.models import Product, ProductCompatibility, Unit
from pydantic import BaseModel, constr
from typing import List, Optional
from app.tools import Tools


class ProductCreateRequest(BaseModel):
    component_ref: str
    model_ids: List[int]
    title: constr(min_length=16, max_length=70)
    description: Optional[str] = None
    reference_price: int


class ProductResponse(BaseModel):
    id: int
    component_ref: str
    sku_id: int
    sku: str
    title: str
    description: Optional[str] = None
    reference_price: int
    compatible_models: List[int]


router = APIRouter()


@router.post("/", response_model=ProductResponse)
def create_product(product_data: ProductCreateRequest,
                   db: Session = Depends(get_db)):

    try:
        # validate component existance
        component = db.query(Component).filter(
            Component.ref == product_data.component_ref).first()
        if not component:
            raise HTTPException(status_code=400,
                                detail=f"\
                                Component {product_data.component_ref} not found")

        # validate all mode ids exist
        for model_id in product_data.model_ids:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise HTTPException(status_code=400,
                                    detail=f"\
                                    Model ID {model_id} not found")

        # Generate next SKU id for this component
        max_sku = db.query(Product).filter(Product.component_ref ==
                                           product_data.component_ref).order_by(Product.sku_id.desc()).first()

        next_sku_id = (max_sku.sku_id + 1) if max_sku else 1
        sku = product_data.component_ref + str(next_sku_id)

        # create product
        new_product = Product(
            component_ref=product_data.component_ref,
            sku_id=next_sku_id,
            sku=sku,
            title=product_data.title,
            description=product_data.description,
            reference_price=product_data.reference_price
        )

        db.add(new_product)
        db.flush()

        # create compability relationships
        for model_id in product_data.model_ids:
            compatibility = ProductCompatibility(
                product_id=new_product.id,
                model_id=model_id
            )
            db.add(compatibility)

        db.commit()
        db.refresh(new_product)

        return ProductResponse(
            id=new_product.id,
            component_ref=new_product.component_ref,
            sku_id=new_product.sku_id,
            sku=new_product.sku,
            title=new_product.title,
            description=new_product.description,
            reference_price=new_product.reference_price,
            compatible_models=product_data.model_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get("/")
def get_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        return [
            {
                "id": p.id,
                "sku": p.sku,
                "title": p.title,
                "description": p.description,
                "reference_price": p.reference_price,
                "component_ref": p.component_ref
            }
            for p in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch products: {str(e)}")


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        component = db.query(Component).filter(
            Component.ref == product.component_ref).first()

        compabilities = db.query(ProductCompatibility).filter(
            ProductCompatibility.product_id == product_id
        ).all()

        compatible_models = []
        for comp in compabilities:
            model = db.query(Model).filter(Model.id == comp.model_id).first()
            make = db.query(Make).filter(Make.id == model.make_id).first()
            compatible_models.append({
                "model_id": model.id,
                "model_name": model.name,
                "make_name": make.name,
                "years": f"{model.start_year}-{model.end_year}"
            })

        return {
            "id": product.id,
            "sku": product.sku,
            "title": product.title,
            "description": product.description,
            "reference_price": product.reference_price,
            "component_ref": product.component_ref,
            "component_name": component.name,
            "compatible_models": compatible_models,
            "created_at": product.created_at.strftime('%Y-%m-%d %H:%M') if product.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch product: {str(e)}"
        )


@router.get("/{product_id}/units")
def get_product_units(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        units = db.query(Unit).filter(
            Unit.product_id == product_id).all()
        if not units:
            raise HTTPException(status_code=404, detail="Units not found")

        return [
            {
                "id": i.id,
                "sku": i.sku,
                "full_reference": f"{product.sku}-{i.sku}",
                "selling_price": i.selling_price,
                "status": i.status,
                "km": i.km,
                "observations": i.observations,
                "title_suffix": i.title_suffix
            }
            for i in units
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch units for product {product_id}: {str(e)}")
