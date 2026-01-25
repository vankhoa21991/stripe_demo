"""Stripe synchronization service."""
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import Client

from app.stripe_client import create_product, update_product, create_price, deactivate_price


def sync_product_to_stripe(supabase: Client, product: Dict[str, Any], deactivate_old_price: bool = True) -> tuple[bool, Optional[str]]:
    """
    Sync product to Stripe.
    Returns (success, error_message).
    """
    try:
        # Get images from product (handle both images array and image_url for backward compat)
        images = product.get("images", [])
        if not images and product.get("image_url"):
            images = [product["image_url"]]
        
        # Create or update Stripe Product
        if not product.get("stripe_product_id"):
            # Create new product
            stripe_product = create_product(
                title=product["title"],
                description=product.get("description"),
                images=images if images else None
            )
            stripe_product_id = stripe_product.id
        else:
            # Update existing product
            stripe_product_id = product["stripe_product_id"]
            update_product(
                stripe_product_id=stripe_product_id,
                title=product["title"],
                description=product.get("description"),
                images=images if images else None
            )
        
        # Handle price
        old_price_id = product.get("active_stripe_price_id")
        
        # Create new price (Stripe doesn't allow updating prices)
        new_price = create_price(
            product_id=stripe_product_id,
            amount=product["current_price_amount"],
            currency=product.get("currency", "usd")
        )
        
        # Deactivate old price if requested
        if old_price_id and deactivate_old_price:
            try:
                deactivate_price(old_price_id)
            except Exception:
                # Ignore errors when deactivating old price
                pass
        
        # Update product in Supabase
        update_data = {
            "stripe_product_id": stripe_product_id,
            "active_stripe_price_id": new_price.id,
            "last_sync_status": "success",
            "last_sync_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("products").update(update_data).eq("id", product["id"]).execute()
        
        return True, None
        
    except Exception as e:
        # Update product with error status
        update_data = {
            "last_sync_status": f"failed: {str(e)}",
            "last_sync_at": datetime.utcnow().isoformat()
        }
        supabase.table("products").update(update_data).eq("id", product["id"]).execute()
        return False, str(e)


def resync_product(supabase: Client, product_id: int) -> tuple[bool, Optional[str]]:
    """Resync a product to Stripe."""
    result = supabase.table("products").select("*").eq("id", product_id).is_("deleted_at", "null").execute()
    if not result.data:
        return False, "Product not found"
    
    product = result.data[0]
    return sync_product_to_stripe(supabase, product)
