from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Make, Model, Component, Product, Unit, ProductCompatibility
from typing import List, Optional
import httpx

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Homepage/Dashboard


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Product creation form


@router.get("/products/new", response_class=HTMLResponse)
async def product_form(request: Request, db: Session = Depends(get_db)):
    components = db.query(Component).all()
    makes = db.query(Make).all()
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "components": components,
        "makes": makes
    })


@router.post("/products/new")
async def create_product_form(
    request: Request,
    component_ref: str = Form(...),
    title: str = Form(...),
    model_ids: List[int] = Form(...),
    description: str = Form(""),
    reference_price: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Call your existing API endpoint internally
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/products",
                json={
                    "component_ref": component_ref,
                    "title": title,
                    "model_ids": model_ids,
                    "description": description,
                    "reference_price": reference_price
                }
            )

        if response.status_code == 200:
            product_data = response.json()
            return RedirectResponse(
                url=f"/products/{product_data['id']}",
                status_code=303
            )
        else:
            error_msg = response.json().get("detail", "Error creating product")
            components = db.query(Component).all()
            makes = db.query(Make).all()
            return templates.TemplateResponse("product_form.html", {
                "request": request,
                "components": components,
                "makes": makes,
                "error": error_msg
            })

    except Exception as e:
        components = db.query(Component).all()
        makes = db.query(Make).all()
        return templates.TemplateResponse("product_form.html", {
            "request": request,
            "components": components,
            "makes": makes,
            "error": f"Error: {str(e)}"
        })

# Unit creation form


@router.get("/units/new", response_class=HTMLResponse)
async def unit_form(request: Request, product_id: Optional[int] = None, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    selected_product = None
    if product_id:
        selected_product = db.query(Product).filter(
            Product.id == product_id).first()

    return templates.TemplateResponse("unit_form.html", {
        "request": request,
        "products": products,
        "selected_product": selected_product
    })


@router.post("/units/new")
async def create_unit_form(
    request: Request,
    product_id: int = Form(...),
    alternative_sku: Optional[str] = Form(""),
    selling_price: int = Form(...),
    km: Optional[int] = Form(None),
    observations: Optional[str] = Form(""),
    status: str = Form("active"),
    db: Session = Depends(get_db)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/units",
                json={
                    "product_id": product_id,
                    "alternative_sku": alternative_sku,
                    "selling_price": selling_price,
                    "km": km or 0,
                    "observations": observations,
                    "status": status
                }
            )

        if response.status_code == 200:
            unit_data = response.json()
            return RedirectResponse(
                url=f"/units/{unit_data['id']}",
                status_code=303
            )
        else:
            error_msg = response.json().get("detail", "Error creating unit")
            products = db.query(Product).all()
            return templates.TemplateResponse("unit_form.html", {
                "request": request,
                "products": products,
                "error": error_msg
            })

    except Exception as e:
        products = db.query(Product).all()
        return templates.TemplateResponse("unit_form.html", {
            "request": request,
            "products": products,
            "error": f"Error: {str(e)}"
        })

# Search functionality


@router.get("/search", response_class=HTMLResponse)
async def search_results(request: Request, q: str = ""):
    # if not q:
    #     return templates.TemplateResponse("search_results.html", {
    #         "request": request,
    #         "query": q,
    #         "products": [],
    #         "units": []
    #     })

    try:
        async with httpx.AsyncClient() as client:
            # Search products and units
            products_response = await client.get(f"http://localhost:8000/api/search/products?q={q}")
            units_response = await client.get(f"http://localhost:8000/api/search/units?q={q}")

            products = products_response.json() if products_response.status_code == 200 else []
            units = units_response.json() if units_response.status_code == 200 else []

        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "query": q,
            "products": products,
            "units": units
        })

    except Exception as e:
        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "query": q,
            "products": [],
            "units": [],
            "error": f"Search error: {str(e)}"
        })


# Product detail page
@router.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    try:
        async with httpx.AsyncClient() as client:
            # Get product details and units
            product_response = await client.get(f"http://localhost:8000/api/products/{product_id}")
            units_response = await client.get(f"http://localhost:8000/api/products/{product_id}/units")

            if product_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Product not found")

            product = product_response.json()
            units = units_response.json() if units_response.status_code == 200 else []

        return templates.TemplateResponse("product_detail.html", {
            "request": request,
            "product": product,
            "units": units
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading product: {str(e)}")


# Unit detail page
@router.get("/units/{unit_id}", response_class=HTMLResponse)
async def unit_detail(request: Request, unit_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/units/{unit_id}")

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Unit not found")

            unit = response.json()

        return templates.TemplateResponse("unit_detail.html", {
            "request": request,
            "unit": unit
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading unit: {str(e)}")


# AJAX endpoint for models by make
@router.get("/makes/{make_id}/models")
async def get_models_for_make(make_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/makes/{make_id}/models")
            return response.json()
    except Exception:
        return []


@router.get("/products/{product_id}/photos/new", response_class=HTMLResponse)
async def product_photo_upload_page(request: Request, product_id: int):
    """Photo upload page for a product"""
    try:
        async with httpx.AsyncClient() as client:
            # Get product details
            product_response = await client.get(f"http://localhost:8000/api/products/{product_id}")
            if product_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Product not found")

            product = product_response.json()

            # Get existing photos
            photos_response = await client.get(f"http://localhost:8000/api/products/{product_id}/photos")
            photos = photos_response.json() if photos_response.status_code == 200 else []

            return templates.TemplateResponse("product_photo_upload.html", {
                "request": request,
                "product": product,
                "photos": photos,
                "photo_count": len(photos)
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading photo upload page: {str(e)}")


@router.get("/units/{unit_id}/photos/new", response_class=HTMLResponse)
async def unit_photo_upload_page(request: Request, unit_id: int):
    """Photo upload page for an unit"""
    try:
        async with httpx.AsyncClient() as client:
            # Get unit details
            unit_response = await client.get(f"http://localhost:8000/api/units/{unit_id}")
            if unit_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Unit not found")

            unit = unit_response.json()

            # Get existing photos
            photos_response = await client.get(f"http://localhost:8000/api/units/{unit_id}/photos")
            photos = photos_response.json() if photos_response.status_code == 200 else []

            return templates.TemplateResponse("unit_photo_upload.html", {
                "request": request,
                "unit": unit,
                "photos": photos,
                "photo_count": len(photos)
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading photo upload page: {str(e)}")
