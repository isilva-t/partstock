from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Make, Model
from app.models import Category, SubCategory, Component
from app.models import Product, ProductCompatibility, Unit
from pydantic import BaseModel
from typing import List, Optional
from app.tools import Tools


class ProductCreateRequest(BaseModel):
    component_ref: str
    model_ids: List[int]
    title: str
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


class UnitCreateRequest(BaseModel):
    product_id: int
    year_month: str = None
    alternative_sku: str = None
    selling_price: int
    km: int = None  # motor kilometers
    observations: Optional[str] = None
    status: str = "active"  # active|sold|incomplete|consume


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


router = APIRouter(prefix="/api", tags=["api"])


@router.get("/")
def read_root():
    return {"message": "API is fking running!!!"}


@router.get("/makes")
def get_makes(db: Session = Depends(get_db)):
    try:
        makes = db.query(Make).all()
        return [{"id": make.id, "name": make.name} for make in makes]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch makes: {str(e)}")


@router.get("/makes/{make_id}/models")
def get_models_by_make(make_id: int, db: Session = Depends(get_db)):
    try:
        models = db.query(Model).filter(Model.make_id == make_id).all()
        return [{"id": model.id,
                 "name": model.name,
                 "start_year": model.start_year,
                 "end_year": model.end_year} for model in models]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch models for make {make_id}: {str(e)}")


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    try:
        categories = db.query(Category).all()
        return [{"id": cat.id, "name": cat.name} for cat in categories]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch categories: {str(e)}")


@router.get("/categories/{category_id}/sub-categories")
def get_sub_categories(category_id: int, db: Session = Depends(get_db)):
    try:
        sub_cats = db.query(SubCategory).filter(
            SubCategory.category_id == category_id).all()
        return [{"id": sc.id,
                 "name": sc.name,
                 "ref_example": sc.ref_example} for sc in sub_cats]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch sub-categories for category \
                            {category_id}: {str(e)}")


@router.get("/sub-categories")
def get_all_sub_categories(db: Session = Depends(get_db)):
    try:
        sub_categories = db.query(SubCategory).all()
        return [{"id": sc.id, "category_id": sc.category_id, "name": sc.name, "ref_example": sc.ref_example} for sc in sub_categories]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch sub-categories: {str(e)}")


@router.get("/components")
def get_components(db: Session = Depends(get_db)):
    """Get all components"""
    try:
        components = db.query(Component).all()
        return [{"id": comp.id,
                 "sub_category_id": comp.sub_category_id,
                 "name": comp.name,
                 "ref": comp.ref} for comp in components]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch components: {str(e)}")


@router.get("/categories/{category_id}/components")
def get_components_by_category(category_id: int, db: Session = Depends(get_db)):
    """Get all components for a specific category"""
    try:
        # Join Component -> SubCategory -> Category to get components for this category
        components = db.query(Component).join(SubCategory).filter(
            SubCategory.category_id == category_id
        ).all()

        return [{"id": comp.id,
                 "sub_category_id": comp.sub_category_id,
                 "name": comp.name,
                 "ref": comp.ref} for comp in components]

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch components for category {category_id}: {str(e)}")


@router.get("/sub-categories/{sub_category_id}/components")
def get_components_by_sub_category(sub_category_id: int, db: Session = Depends(get_db)):
    """Get all components for a specific sub-category"""
    try:
        components = db.query(Component).filter(
            Component.sub_category_id == sub_category_id
        ).all()

        return [{"id": comp.id,
                 "sub_category_id": comp.sub_category_id,
                 "name": comp.name,
                 "ref": comp.ref} for comp in components]

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch components for sub-category {sub_category_id}: {str(e)}")


@router.post("/products", response_model=ProductResponse)
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


@router.get("/products")
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


@router.get("/products/{product_id}")
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


@router.post("/units", response_model=UnitResponse)
def create_unit(unit_data: UnitCreateRequest,
                db: Session = Depends(get_db)):
    try:
        # validate product exists
        product = db.query(Product).filter(
            Product.id == unit_data.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product ID {
                                unit_data.product_id} not found")

        print("hello here")
        unit_data.year_month = Tools.get_cur_year_month()
        print("and here")
        print(unit_data.year_month)
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
            status=unit_data.status
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
            product_sku=product.sku
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create unit: {str(e)}"
        )


@router.get("/units")
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
                "description": i.product.description
            }
            for i in units
        ]
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch units: {str(e)}")


@router.get("/units/{unit_id}")
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
            "created_at": unit.created_at.strftime('%Y-%m-%d %H:%M') if unit.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch unit: {str(e)}"
        )


@router.get("/products/{product_id}/units")
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
                "observations": i.observations
            }
            for i in units
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch units for product {product_id}: {str(e)}")


@router.get("/search/products")
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
                "title": p.title if p.title else None,
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


@router.get("/search/units")
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
                "description": i.product.description
            }
            for i in units
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
