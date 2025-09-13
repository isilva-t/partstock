from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Make, Model
from app.models import Category, SubCategory, Component

router = APIRouter()


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
