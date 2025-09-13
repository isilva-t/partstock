from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Make, Model, Component, Product, Instance, ProductCompatibility
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

# Instance creation form


@router.get("/instances/new", response_class=HTMLResponse)
async def instance_form(request: Request, product_id: Optional[int] = None, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    selected_product = None
    if product_id:
        selected_product = db.query(Product).filter(
            Product.id == product_id).first()

    return templates.TemplateResponse("instance_form.html", {
        "request": request,
        "products": products,
        "selected_product": selected_product
    })


@router.post("/instances/new")
async def create_instance_form(
    request: Request,
    product_id: int = Form(...),
    year_month: str = Form(...),
    alternative_sku: str = Form(""),
    selling_price: int = Form(...),
    km: Optional[int] = Form(None),
    observations: str = Form(""),
    status: str = Form("active"),
    db: Session = Depends(get_db)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/instances",
                json={
                    "product_id": product_id,
                    "year_month": year_month,
                    "alternative_sku": alternative_sku or None,
                    "selling_price": selling_price,
                    "km": km,
                    "observations": observations,
                    "status": status
                }
            )

        if response.status_code == 200:
            instance_data = response.json()
            return RedirectResponse(
                url=f"/instances/{instance_data['id']}",
                status_code=303
            )
        else:
            error_msg = response.json().get("detail", "Error creating instance")
            products = db.query(Product).all()
            return templates.TemplateResponse("instance_form.html", {
                "request": request,
                "products": products,
                "error": error_msg
            })

    except Exception as e:
        products = db.query(Product).all()
        return templates.TemplateResponse("instance_form.html", {
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
    #         "instances": []
    #     })

    try:
        async with httpx.AsyncClient() as client:
            # Search products and instances
            products_response = await client.get(f"http://localhost:8000/api/search/products?q={q}")
            instances_response = await client.get(f"http://localhost:8000/api/search/instances?q={q}")

            products = products_response.json() if products_response.status_code == 200 else []
            instances = instances_response.json() if instances_response.status_code == 200 else []

        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "query": q,
            "products": products,
            "instances": instances
        })

    except Exception as e:
        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "query": q,
            "products": [],
            "instances": [],
            "error": f"Search error: {str(e)}"
        })


# Product detail page
@router.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    try:
        async with httpx.AsyncClient() as client:
            # Get product details and instances
            product_response = await client.get(f"http://localhost:8000/api/products/{product_id}")
            instances_response = await client.get(f"http://localhost:8000/api/products/{product_id}/instances")

            if product_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Product not found")

            product = product_response.json()
            instances = instances_response.json() if instances_response.status_code == 200 else []

        return templates.TemplateResponse("product_detail.html", {
            "request": request,
            "product": product,
            "instances": instances
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading product: {str(e)}")


# Instance detail page
@router.get("/instances/{instance_id}", response_class=HTMLResponse)
async def instance_detail(request: Request, instance_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/instances/{instance_id}")

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Instance not found")

            instance = response.json()

        return templates.TemplateResponse("instance_detail.html", {
            "request": request,
            "instance": instance
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading instance: {str(e)}")


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


@router.get("/instances/{instance_id}/photos/new", response_class=HTMLResponse)
async def instance_photo_upload_page(request: Request, instance_id: int):
    """Photo upload page for an instance"""
    try:
        async with httpx.AsyncClient() as client:
            # Get instance details
            instance_response = await client.get(f"http://localhost:8000/api/instances/{instance_id}")
            if instance_response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="Instance not found")

            instance = instance_response.json()

            # Get existing photos
            photos_response = await client.get(f"http://localhost:8000/api/instances/{instance_id}/photos")
            photos = photos_response.json() if photos_response.status_code == 200 else []

            return templates.TemplateResponse("instance_photo_upload.html", {
                "request": request,
                "instance": instance,
                "photos": photos,
                "photo_count": len(photos)
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading photo upload page: {str(e)}")
