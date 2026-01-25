"""Order service for business logic."""
from typing import Dict, Any, List
from supabase import Client
from app.schemas import CheckoutItem


def create_order_from_checkout(
    supabase: Client,
    items: List[CheckoutItem],
    stripe_checkout_session_id: str
) -> Dict[str, Any]:
    """Create an order from checkout items."""
    total_amount = 0
    order_items = []
    
    for item in items:
        # Get product from Supabase
        result = supabase.table("products").select("*").eq("id", item.product_id).is_("deleted_at", "null").eq("published", True).execute()
        
        if not result.data:
            raise ValueError(f"Product {item.product_id} not found or not published")
        
        product = result.data[0]
        
        if not product.get("active_stripe_price_id"):
            raise ValueError(f"Product {item.product_id} has no active Stripe price")
        
        item_total = product["current_price_amount"] * item.quantity
        total_amount += item_total
        
        order_items.append({
            "product_id": product["id"],
            "quantity": item.quantity,
            "stripe_price_id_used": product["active_stripe_price_id"],
            "unit_amount_snapshot": product["current_price_amount"]
        })
    
    # Create order
    order_data = {
        "status": "pending_payment",
        "stripe_checkout_session_id": stripe_checkout_session_id,
        "total_amount_snapshot": total_amount,
        "currency": "usd"  # Assuming single currency for simplicity
    }
    
    order_result = supabase.table("orders").insert(order_data).execute()
    order = order_result.data[0] if order_result.data else None
    
    if not order:
        raise ValueError("Failed to create order")
    
    # Create order items
    for item_data in order_items:
        item_data["order_id"] = order["id"]
        supabase.table("order_items").insert(item_data).execute()
    
    # Fetch complete order with items
    order_result = supabase.table("orders").select("*, order_items(*)").eq("id", order["id"]).execute()
    return order_result.data[0] if order_result.data else order


def update_order_status(supabase: Client, stripe_checkout_session_id: str, status: str, customer_email: str = None) -> Dict[str, Any]:
    """Update order status from webhook."""
    result = supabase.table("orders").select("*").eq("stripe_checkout_session_id", stripe_checkout_session_id).execute()
    
    if not result.data:
        raise ValueError("Order not found")
    
    order = result.data[0]
    
    update_data = {"status": status}
    if customer_email:
        update_data["customer_email"] = customer_email
    
    result = supabase.table("orders").update(update_data).eq("id", order["id"]).execute()
    return result.data[0] if result.data else order
