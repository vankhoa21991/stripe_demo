"""SQLAlchemy database models."""
from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    currency = Column(String(3), nullable=False, default="usd")
    current_price_amount = Column(Integer, nullable=False)  # in minor units (cents)
    published = Column(Boolean, default=False)
    
    # Stripe integration fields
    stripe_product_id = Column(String(255), nullable=True)
    active_stripe_price_id = Column(String(255), nullable=True)
    last_sync_status = Column(String(50), nullable=True)  # 'success', 'failed', 'pending'
    last_sync_at = Column(TIMESTAMP, nullable=True)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)  # soft delete
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    """Order model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), nullable=False, default="pending_payment")  # 'pending_payment', 'paid', 'failed', 'cancelled'
    stripe_checkout_session_id = Column(String(255), unique=True, nullable=True)
    total_amount_snapshot = Column(Integer, nullable=False)  # in minor units
    currency = Column(String(3), nullable=False, default="usd")
    customer_email = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Order item model."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    stripe_price_id_used = Column(String(255), nullable=False)
    unit_amount_snapshot = Column(Integer, nullable=False)  # price at time of checkout
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class StripeEvent(Base):
    """Stripe event tracking for idempotency."""
    __tablename__ = "stripe_events"
    
    id = Column(Integer, primary_key=True, index=True)
    stripe_event_id = Column(String(255), unique=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
