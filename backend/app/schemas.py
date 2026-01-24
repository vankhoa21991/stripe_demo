"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Product Schemas
class ProductBase(BaseModel):
    """Base product schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None  # Backward compatibility
    images: Optional[List[str]] = Field(default_factory=list)  # Multiple images
    category: Optional[str] = None
    currency: str = Field(default="usd", max_length=3)
    current_price_amount: int = Field(..., gt=0)  # in minor units (cents)
    published: bool = False


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None  # Backward compatibility
    images: Optional[List[str]] = None  # Multiple images
    category: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    current_price_amount: Optional[int] = Field(None, gt=0)
    published: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    stripe_product_id: Optional[str] = None
    active_stripe_price_id: Optional[str] = None
    last_sync_status: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    formatted_price: Optional[str] = None  # Added for display convenience
    images: List[str] = Field(default_factory=list)  # Override to ensure it's always a list
    
    class Config:
        from_attributes = True


class ProductPublic(ProductBase):
    """Public product schema (for storefront, excludes admin fields)."""
    id: int
    formatted_price: str  # e.g., "$19.99"
    images: List[str] = Field(default_factory=list)  # Override to ensure it's always a list
    
    class Config:
        from_attributes = True


# Checkout Schemas
class CheckoutItem(BaseModel):
    """Schema for checkout item."""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CheckoutSessionRequest(BaseModel):
    """Schema for creating checkout session."""
    items: List[CheckoutItem] = Field(..., min_items=1)
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Schema for checkout session response."""
    checkout_url: str
    session_id: str


# Order Schemas
class OrderItemResponse(BaseModel):
    """Schema for order item response."""
    product_id: int
    quantity: int
    unit_amount_snapshot: int
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: int
    status: str
    total_amount_snapshot: int
    currency: str
    customer_email: Optional[str] = None
    items: List[OrderItemResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True
