"""Stripe synchronization service."""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Product
from app.stripe_client import create_product, update_product, create_price, deactivate_price


def sync_product_to_stripe(db: Session, product: Product, deactivate_old_price: bool = True) -> tuple[bool, Optional[str]]:
    """
    Sync product to Stripe.
    Returns (success, error_message).
    """
    try:
        # Create or update Stripe Product
        if not product.stripe_product_id:
            # Create new product
            stripe_product = create_product(
                title=product.title,
                description=product.description,
                images=[product.image_url] if product.image_url else None
            )
            product.stripe_product_id = stripe_product.id
        else:
            # Update existing product
            update_product(
                stripe_product_id=product.stripe_product_id,
                title=product.title,
                description=product.description,
                images=[product.image_url] if product.image_url else None
            )
        
        # Handle price
        old_price_id = product.active_stripe_price_id
        
        # Create new price (Stripe doesn't allow updating prices)
        new_price = create_price(
            product_id=product.stripe_product_id,
            amount=product.current_price_amount,
            currency=product.currency
        )
        
        # Deactivate old price if requested
        if old_price_id and deactivate_old_price:
            try:
                deactivate_price(old_price_id)
            except Exception:
                # Ignore errors when deactivating old price
                pass
        
        product.active_stripe_price_id = new_price.id
        product.last_sync_status = "success"
        product.last_sync_at = datetime.utcnow()
        
        db.commit()
        return True, None
        
    except Exception as e:
        product.last_sync_status = f"failed: {str(e)}"
        product.last_sync_at = datetime.utcnow()
        db.commit()
        return False, str(e)


def resync_product(db: Session, product_id: int) -> tuple[bool, Optional[str]]:
    """Resync a product to Stripe."""
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
    if not product:
        return False, "Product not found"
    
    return sync_product_to_stripe(db, product)
