"""Product API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
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
def get_public_products(db: Session = Depends(get_db)):
    """Get published products for storefront."""
    products = get_products(db, published_only=True)
    return {
        "products": [
            ProductPublic(
                id=product.id,
                title=product.title,
                description=product.description,
                image_url=product.image_url,
                currency=product.currency,
                current_price_amount=product.current_price_amount,
                published=product.published,
                formatted_price=format_price(product.current_price_amount, product.currency)
            )
            for product in products
        ]
    }


@router.get("/admin", response_model=List[ProductResponse])
def get_admin_products(db: Session = Depends(get_db)):
    """Get all products (including unpublished) for admin."""
    products = get_products(db, published_only=False)
    # Add formatted_price for admin display
    return [
        ProductResponse(
            id=product.id,
            title=product.title,
            description=product.description,
            image_url=product.image_url,
            currency=product.currency,
            current_price_amount=product.current_price_amount,
            published=product.published,
            stripe_product_id=product.stripe_product_id,
            active_stripe_price_id=product.active_stripe_price_id,
            last_sync_status=product.last_sync_status,
            last_sync_at=product.last_sync_at,
            created_at=product.created_at,
            updated_at=product.updated_at,
            formatted_price=format_price(product.current_price_amount, product.currency)
        )
        for product in products
    ]


@router.post("/admin", response_model=ProductResponse, status_code=201)
def create_admin_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    return create_product(db, product_data)


@router.put("/admin/{product_id}", response_model=ProductResponse)
def update_admin_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product."""
    try:
        return update_product(db, product_id, product_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/admin/{product_id}")
def delete_admin_product(product_id: int, db: Session = Depends(get_db)):
    """Soft delete a product."""
    success = delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}


@router.post("/admin/{product_id}/resync")
def resync_admin_product(product_id: int, db: Session = Depends(get_db)):
    """Resync a product to Stripe."""
    success, error = resync_product(db, product_id)
    if not success:
        raise HTTPException(status_code=400, detail=error or "Resync failed")
    return {"success": True, "message": "Product synced successfully"}
