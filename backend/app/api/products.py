"""Product API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.database import get_supabase
from app.schemas import ProductCreate, ProductUpdate, ProductResponse, ProductPublic
from app.services.product_service import (
    create_product,
    update_product,
    delete_product,
    get_products,
    get_product,
    format_price
)
from app.services.stripe_sync import resync_product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=dict)
def get_public_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    supabase: Client = Depends(get_supabase)
):
    """Get published products for storefront."""
    products = get_products(supabase, published_only=True, category=category, search=search)
    return {
        "products": [
            ProductPublic(
                id=product["id"],
                title=product["title"],
                description=product.get("description"),
                image_url=product.get("images", [None])[0] if product.get("images") else None,  # Backward compat
                images=product.get("images", []),
                category=product.get("category"),
                currency=product["currency"],
                current_price_amount=product["current_price_amount"],
                published=product.get("published", False),
                formatted_price=format_price(product["current_price_amount"], product["currency"])
            )
            for product in products
        ]
    }


@router.get("/admin", response_model=List[ProductResponse])
def get_admin_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    supabase: Client = Depends(get_supabase)
):
    """Get all products (including unpublished) for admin."""
    products = get_products(supabase, published_only=False, category=category, search=search)
    # Add formatted_price for admin display
    return [
        ProductResponse(
            id=product["id"],
            title=product["title"],
            description=product.get("description"),
            image_url=product.get("images", [None])[0] if product.get("images") else None,  # Backward compat
            images=product.get("images", []),
            category=product.get("category"),
            currency=product["currency"],
            current_price_amount=product["current_price_amount"],
            published=product.get("published", False),
            stripe_product_id=product.get("stripe_product_id"),
            active_stripe_price_id=product.get("active_stripe_price_id"),
            last_sync_status=product.get("last_sync_status"),
            last_sync_at=product.get("last_sync_at"),
            created_at=product["created_at"],
            updated_at=product["updated_at"],
            formatted_price=format_price(product["current_price_amount"], product["currency"])
        )
        for product in products
    ]


@router.post("/admin", response_model=ProductResponse, status_code=201)
def create_admin_product(product_data: ProductCreate, supabase: Client = Depends(get_supabase)):
    """Create a new product."""
    product = create_product(supabase, product_data)
    return ProductResponse(
        id=product["id"],
        title=product["title"],
        description=product.get("description"),
        image_url=product.get("images", [None])[0] if product.get("images") else None,
        images=product.get("images", []),
        category=product.get("category"),
        currency=product["currency"],
        current_price_amount=product["current_price_amount"],
        published=product.get("published", False),
        stripe_product_id=product.get("stripe_product_id"),
        active_stripe_price_id=product.get("active_stripe_price_id"),
        last_sync_status=product.get("last_sync_status"),
        last_sync_at=product.get("last_sync_at"),
        created_at=product["created_at"],
        updated_at=product["updated_at"],
        formatted_price=format_price(product["current_price_amount"], product["currency"])
    )


@router.put("/admin/{product_id}", response_model=ProductResponse)
def update_admin_product(product_id: int, product_data: ProductUpdate, supabase: Client = Depends(get_supabase)):
    """Update a product."""
    try:
        product = update_product(supabase, product_id, product_data)
        return ProductResponse(
            id=product["id"],
            title=product["title"],
            description=product.get("description"),
            image_url=product.get("images", [None])[0] if product.get("images") else None,
            images=product.get("images", []),
            category=product.get("category"),
            currency=product["currency"],
            current_price_amount=product["current_price_amount"],
            published=product.get("published", False),
            stripe_product_id=product.get("stripe_product_id"),
            active_stripe_price_id=product.get("active_stripe_price_id"),
            last_sync_status=product.get("last_sync_status"),
            last_sync_at=product.get("last_sync_at"),
            created_at=product["created_at"],
            updated_at=product["updated_at"],
            formatted_price=format_price(product["current_price_amount"], product["currency"])
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/admin/{product_id}")
def delete_admin_product(product_id: int, supabase: Client = Depends(get_supabase)):
    """Soft delete a product."""
    success = delete_product(supabase, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}


@router.post("/admin/{product_id}/resync")
def resync_admin_product(product_id: int, supabase: Client = Depends(get_supabase)):
    """Resync a product to Stripe."""
    success, error = resync_product(supabase, product_id)
    if not success:
        raise HTTPException(status_code=400, detail=error or "Resync failed")
    return {"success": True, "message": "Product synced successfully"}
