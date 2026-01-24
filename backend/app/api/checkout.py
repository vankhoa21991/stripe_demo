"""Checkout API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.database import get_supabase
from app.config import settings
from app.schemas import CheckoutSessionRequest, CheckoutSessionResponse
from app.services.order_service import create_order_from_checkout
from app.stripe_client import create_checkout_session

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/session", response_model=CheckoutSessionResponse)
def create_checkout(checkout_data: CheckoutSessionRequest, supabase: Client = Depends(get_supabase)):
    """Create Stripe Checkout Session."""
    # Build line items for Stripe
    line_items = []
    for item in checkout_data.items:
        result = supabase.table("products").select("*").eq("id", item.product_id).is_("deleted_at", "null").eq("published", True).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found or not published")
        
        product = result.data[0]
        
        if not product.get("active_stripe_price_id"):
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} has no active Stripe price")
        
        line_items.append({
            "price": product["active_stripe_price_id"],
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
        create_order_from_checkout(supabase, checkout_data.items, session.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return CheckoutSessionResponse(
        checkout_url=session.url,
        session_id=session.id
    )
