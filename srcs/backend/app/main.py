from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import Make, Model
from app.models import Category, SubCategory, Component


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
    return [{"id": comp.id, "name": comp.name, "ref": comp.ref} for comp in components]
