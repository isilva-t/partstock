from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import Make, Model
from app.models import Category, SubCategory, Component
from app.models import Product, ProductCompatibility
from pydantic import BaseModel
from typing import List


class ProductCreateRequest(BaseModel):
    component_ref: str
    model_ids: List[int]
    description: str
    reference_price: int


class ProductResponse(BaseModel):
    id: int
    component_ref: str
    sku_id: int
    sku: str
    description: str
    reference_price: int
    compatible_models: List[int]


Base.metadata.create_all(bind=engine)


app = FastAPI(title="PartStock")


@app.get("/")
def read_root():
    return {"message": "API is fking running!!!"}


@app.get("/makes")
def get_makes(db: Session = Depends(get_db)):
    makes = db.query(Make).all()
    return [{"id": make.id, "name": make.name} for make in makes]


@app.get("/makes/{make_id}/models")
def get_models_by_make(make_id: int, db: Session = Depends(get_db)):
    models = db.query(Model).filter(Model.make_id == make_id).all()
    return [{"id": model.id,
             "name": model.name,
             "start_year": model.start_year,
             "end_year": model.end_year} for model in models]


@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return [{"id": cat.id, "name": cat.name} for cat in categories]


@app.get("/categories/{category_id}/sub-categories")
def get_sub_categories(category_id: int, db: Session = Depends(get_db)):
    sub_cats = db.query(SubCategory).filter(
        SubCategory.category_id == category_id).all()
    return [{"id": sc.id,
             "name": sc.name,
             "ref_example": sc.ref_example} for sc in sub_cats]


@app.get("/components")
def get_components(db: Session = Depends(get_db)):
    """Get all components"""
    components = db.query(Component).all()
    return [{"id": comp.id,
             "name": comp.name,
             "ref": comp.ref} for comp in components]


@app.post("/products", response_model=ProductResponse)
def create_product(product_data: ProductCreateRequest,
                   db: Session = Depends(get_db)):

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
        description=new_product.description,
        reference_price=new_product.reference_price,
        compatible_models=product_data.model_ids
    )


@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "sku": p.sku,
            "description": p.description,
            "reference_price": p.reference_price,
            "component_ref": p.component_ref
        }
        for p in products
    ]


@app.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
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
        "description": product.description,
        "reference_price": product.reference_price,
        "component_ref": product.component_ref,
        "component_name": component.name,
        "compatible_models": compatible_models,
        "created_at": product.created_at
    }
