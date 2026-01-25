"""Order API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.database import get_supabase
from app.schemas import OrderResponse, OrderItemResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, supabase: Client = Depends(get_supabase)):
    """Get order by ID."""
    # Get order with items
    result = supabase.table("orders").select("*, order_items(*)").eq("id", order_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_data = result.data[0]
    
    # Convert order_items to OrderItemResponse
    items = [
        OrderItemResponse(
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_amount_snapshot=item["unit_amount_snapshot"]
        )
        for item in (order_data.get("order_items") or [])
    ]
    
    return OrderResponse(
        id=order_data["id"],
        status=order_data["status"],
        total_amount_snapshot=order_data["total_amount_snapshot"],
        currency=order_data["currency"],
        customer_email=order_data.get("customer_email"),
        items=items,
        created_at=order_data["created_at"]
    )


@router.get("/by-session/{session_id}", response_model=OrderResponse)
def get_order_by_session(session_id: str, supabase: Client = Depends(get_supabase)):
    """Get order by Stripe Checkout Session ID."""
    # Get order with items
    result = supabase.table("orders").select("*, order_items(*)").eq("stripe_checkout_session_id", session_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_data = result.data[0]
    
    # Convert order_items to OrderItemResponse
    items = [
        OrderItemResponse(
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_amount_snapshot=item["unit_amount_snapshot"]
        )
        for item in (order_data.get("order_items") or [])
    ]
    
    return OrderResponse(
        id=order_data["id"],
        status=order_data["status"],
        total_amount_snapshot=order_data["total_amount_snapshot"],
        currency=order_data["currency"],
        customer_email=order_data.get("customer_email"),
        items=items,
        created_at=order_data["created_at"]
    )
