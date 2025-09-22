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

# Product creation form - GET only (form display)


@router.get("/products/new", response_class=HTMLResponse)
async def product_form(request: Request, db: Session = Depends(get_db)):
    components = db.query(Component).all()
    makes = db.query(Make).all()
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "components": components,
        "makes": makes
    })

# Unit creation form - GET only (form display)


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

# Search functionality


@router.get("/search", response_class=HTMLResponse)
async def search_results(request: Request, q: str = ""):
    try:
        async with httpx.AsyncClient() as client:
            # Use internal backend communication
            products_response = await client.get(f"http://backend:8000/api/v1/search/products?q={q}")
            units_response = await client.get(f"http://backend:8000/api/v1/search/units?q={q}")

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
            product_response = await client.get(f"http://backend:8000/api/v1/products/{product_id}")
            units_response = await client.get(f"http://backend:8000/api/v1/products/{product_id}/units")

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
            response = await client.get(f"http://backend:8000/api/v1/units/{unit_id}")

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
            response = await client.get(f"http://backend:8000/api/v1/catalog/makes/{make_id}/models")
            return response.json()
    except Exception:
        return []


@router.get("/products/{product_id}/photos/new", response_class=HTMLResponse)
async def product_photo_upload_page(request: Request, product_id: int):
    """Photo upload page for a product"""
    try:
        async with httpx.AsyncClient() as client:
            # Get product details
            product_response = await client.get(f"http://backend:8000/api/v1/products/{product_id}")
            if product_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Product not found")

            product = product_response.json()

            # Get existing photos
            photos_response = await client.get(f"http://backend:8000/api/v1/products/{product_id}/photos")
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
            unit_response = await client.get(f"http://backend:8000/api/v1/units/{unit_id}")
            if unit_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Unit not found")

            unit = unit_response.json()

            # Get existing photos
            photos_response = await client.get(f"http://backend:8000/api/v1/units/{unit_id}/photos")
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


@router.get("/olx/drafts", response_class=HTMLResponse)
async def olx_draft_list(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://backend:8000/api/v1/olx/drafts/")
        drafts = resp.json() if resp.status_code == 200 else []
    return templates.TemplateResponse("olx_draft_list.html", {
        "request": request,
        "drafts": drafts
    })


@router.get("/olx/auth", response_class=HTMLResponse)
async def olx_auth_page(request: Request):
    return RedirectResponse(url="/api/v1/olx/auth/status")
