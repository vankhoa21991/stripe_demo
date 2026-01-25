"""Product service for business logic."""
import logging
import time
from typing import List, Optional, Callable
from supabase import Client
from httpx import WriteError, ReadError, ConnectError
from app.schemas import ProductCreate, ProductUpdate
from app.services.stripe_sync import sync_product_to_stripe
from app.database import reset_supabase_client, get_supabase

logger = logging.getLogger(__name__)


def format_price(amount: int, currency: str = "usd") -> str:
    """Format price amount to display string."""
    major_units = amount / 100
    if currency.lower() == "usd":
        return f"${major_units:.2f}"
    elif currency.lower() == "eur":
        return f"€{major_units:.2f}"
    else:
        return f"{major_units:.2f} {currency.upper()}"


def _convert_to_product_dict(data: dict) -> dict:
    """Convert Supabase response to product dict, handling images field."""
    # Handle images: convert from JSONB array or single image_url
    images = data.get("images", [])
    if isinstance(images, str):
        # If it's a string, try to parse as JSON
        import json
        try:
            images = json.loads(images)
        except:
            images = [images] if images else []
    elif not isinstance(images, list):
        images = []
    
    # Backward compatibility: if image_url exists but images is empty, use image_url
    if not images and data.get("image_url"):
        images = [data["image_url"]]
    
    result = {**data, "images": images}
    # Remove image_url if it exists (we use images now)
    if "image_url" in result:
        del result["image_url"]
    return result


def create_product(supabase: Client, product_data: ProductCreate) -> dict:
    """Create a new product and sync to Stripe."""
    # Convert product_data to dict, handling images
    product_dict = product_data.model_dump(exclude_unset=True)
    
    # Handle backward compatibility: if image_url is provided, convert to images array
    if "image_url" in product_dict and product_dict["image_url"]:
        product_dict["images"] = [product_dict["image_url"]]
        del product_dict["image_url"]
    elif "images" not in product_dict:
        product_dict["images"] = []
    
    # Insert into Supabase
    result = supabase.table("products").insert(product_dict).execute()
    product = result.data[0] if result.data else None
    
    if not product:
        raise ValueError("Failed to create product")
    
    # Sync to Stripe
    sync_product_to_stripe(supabase, product)
    
    # Refresh from database
    result = supabase.table("products").select("*").eq("id", product["id"]).execute()
    return _convert_to_product_dict(result.data[0]) if result.data else product


def update_product(supabase: Client, product_id: int, product_data: ProductUpdate) -> dict:
    """Update a product and sync changes to Stripe."""
    # Get existing product
    result = supabase.table("products").select("*").eq("id", product_id).is_("deleted_at", "null").execute()
    if not result.data:
        raise ValueError("Product not found")
    
    product = result.data[0]
    
    # Track if price changed
    price_changed = (
        product_data.current_price_amount is not None and
        product_data.current_price_amount != product["current_price_amount"]
    )
    
    # Convert update data to dict
    update_dict = product_data.model_dump(exclude_unset=True)
    
    # Handle backward compatibility: if image_url is provided, convert to images array
    if "image_url" in update_dict and update_dict["image_url"]:
        update_dict["images"] = [update_dict["image_url"]]
        del update_dict["image_url"]
    
    # Update in Supabase
    if update_dict:
        result = supabase.table("products").update(update_dict).eq("id", product_id).execute()
        product = result.data[0] if result.data else product
    
    # Sync to Stripe if any changes
    sync_product_to_stripe(supabase, product)
    
    # Refresh from database
    result = supabase.table("products").select("*").eq("id", product_id).execute()
    return _convert_to_product_dict(result.data[0]) if result.data else product


def delete_product(supabase: Client, product_id: int) -> bool:
    """Soft delete a product."""
    from datetime import datetime
    
    result = supabase.table("products").select("id").eq("id", product_id).is_("deleted_at", "null").execute()
    if not result.data:
        return False
    
    # Soft delete by setting deleted_at
    supabase.table("products").update({"deleted_at": datetime.utcnow().isoformat()}).eq("id", product_id).execute()
    return True


def _execute_with_retry(supabase: Client, operation_name: str, operation_func: Callable, get_client_func: Optional[Callable] = None):
    """Execute a Supabase operation with retry logic for connection errors.
    
    Args:
        supabase: The Supabase client instance
        operation_name: Name of the operation for logging
        operation_func: Function that executes the operation (takes supabase client as parameter)
        get_client_func: Optional function to get a fresh client (defaults to get_supabase)
    """
    max_retries = 3
    retry_delay = 1.0
    current_client = supabase
    get_client = get_client_func or get_supabase
    
    for attempt in range(max_retries):
        try:
            return operation_func(current_client)
        except (WriteError, ReadError, ConnectError, Exception) as e:
            error_type = type(e).__name__
            if attempt < max_retries - 1:
                logger.warning(
                    f"{operation_name} - Connection error (attempt {attempt + 1}/{max_retries}): "
                    f"{error_type}: {str(e)}. Retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
                # Reset client on connection errors and get a fresh one
                if isinstance(e, (WriteError, ReadError, ConnectError)):
                    try:
                        reset_supabase_client()
                        current_client = get_client()  # Get fresh client
                    except Exception as reset_error:
                        logger.error(f"Failed to reset Supabase client: {reset_error}")
            else:
                logger.error(f"{operation_name} - Failed after {max_retries} attempts: {error_type}: {str(e)}")
                raise


def get_products(
    supabase: Client,
    published_only: bool = False,
    category: Optional[str] = None,
    search: Optional[str] = None
) -> List[dict]:
    """Get products, optionally filtered by published status, category, and search.
    
    Includes retry logic for connection errors.
    """
    def _execute_query(client: Client):
        query = client.table("products").select("*").is_("deleted_at", "null")
        
        if published_only:
            query = query.eq("published", True)
        
        if category:
            query = query.eq("category", category)
        
        if search:
            # Search in title and description using ilike
            # Supabase doesn't support OR directly, so we filter after fetching
            # For better performance, we could use full-text search if available
            pass  # Will filter in Python after fetch
        
        result = query.execute()
        products = result.data if result.data else []
        
        # Filter by search term if provided (case-insensitive)
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if search_lower in (p.get("title") or "").lower() or search_lower in (p.get("description") or "").lower()
            ]
        
        return [_convert_to_product_dict(item) for item in products]
    
    return _execute_with_retry(supabase, "get_products", _execute_query)


def get_product(supabase: Client, product_id: int) -> Optional[dict]:
    """Get a single product by ID."""
    result = supabase.table("products").select("*").eq("id", product_id).is_("deleted_at", "null").execute()
    if not result.data:
        return None
    return _convert_to_product_dict(result.data[0])
