"""Stripe API client wrapper."""
import stripe
from typing import Optional, Dict, Any

from app.config import settings

stripe.api_key = settings.stripe_secret_key


def create_product(title: str, description: Optional[str] = None, images: Optional[list] = None) -> Dict[str, Any]:
    """Create a Stripe product."""
    params = {
        "name": title,
    }
    if description:
        params["description"] = description
    if images:
        params["images"] = images
    
    return stripe.Product.create(**params)


def update_product(stripe_product_id: str, title: Optional[str] = None, description: Optional[str] = None, images: Optional[list] = None) -> Dict[str, Any]:
    """Update a Stripe product."""
    params = {}
    if title:
        params["name"] = title
    if description is not None:
        params["description"] = description
    if images is not None:
        params["images"] = images
    
    if not params:
        return stripe.Product.retrieve(stripe_product_id)
    
    return stripe.Product.modify(stripe_product_id, **params)


def create_price(product_id: str, amount: int, currency: str = "usd") -> Dict[str, Any]:
    """Create a Stripe price."""
    return stripe.Price.create(
        product=product_id,
        unit_amount=amount,
        currency=currency,
    )


def deactivate_price(price_id: str) -> Dict[str, Any]:
    """Deactivate a Stripe price."""
    return stripe.Price.modify(price_id, active=False)


def create_checkout_session(line_items: list, success_url: str, cancel_url: str) -> Dict[str, Any]:
    """Create a Stripe checkout session."""
    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )


def retrieve_checkout_session(session_id: str) -> Dict[str, Any]:
    """Retrieve a Stripe checkout session."""
    return stripe.checkout.Session.retrieve(session_id)
