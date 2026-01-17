"""Checkout API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas import CheckoutSessionRequest, CheckoutSessionResponse
from app.services.order_service import create_order_from_checkout
from app.stripe_client import create_checkout_session

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/session", response_model=CheckoutSessionResponse)
def create_checkout(checkout_data: CheckoutSessionRequest, db: Session = Depends(get_db)):
    """Create Stripe Checkout Session."""
    # Build line items for Stripe
    line_items = []
    for item in checkout_data.items:
        from app.models import Product
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.deleted_at.is_(None),
            Product.published == True
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found or not published")
        
        if not product.active_stripe_price_id:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} has no active Stripe price")
        
        line_items.append({
            "price": product.active_stripe_price_id,
            "quantity": item.quantity,
        })
    
    # Create Stripe Checkout Session
    try:
        session = create_checkout_session(
            line_items=line_items,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")
    
    # Create order in DB
    try:
        create_order_from_checkout(db, checkout_data.items, session.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return CheckoutSessionResponse(
        checkout_url=session.url,
        session_id=session.id
    )
