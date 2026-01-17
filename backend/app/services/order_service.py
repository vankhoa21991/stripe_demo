"""Order service for business logic."""
from sqlalchemy.orm import Session
from app.models import Order, OrderItem, Product
from app.schemas import CheckoutItem


def create_order_from_checkout(
    db: Session,
    items: list[CheckoutItem],
    stripe_checkout_session_id: str
) -> Order:
    """Create an order from checkout items."""
    total_amount = 0
    order_items = []
    
    for item in items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.deleted_at.is_(None),
            Product.published == True
        ).first()
        
        if not product:
            raise ValueError(f"Product {item.product_id} not found or not published")
        
        if not product.active_stripe_price_id:
            raise ValueError(f"Product {item.product_id} has no active Stripe price")
        
        item_total = product.current_price_amount * item.quantity
        total_amount += item_total
        
        order_item = OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            stripe_price_id_used=product.active_stripe_price_id,
            unit_amount_snapshot=product.current_price_amount
        )
        order_items.append(order_item)
    
    order = Order(
        status="pending_payment",
        stripe_checkout_session_id=stripe_checkout_session_id,
        total_amount_snapshot=total_amount,
        currency="usd"  # Assuming single currency for simplicity
    )
    
    order.items = order_items
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order


def update_order_status(db: Session, stripe_checkout_session_id: str, status: str, customer_email: str = None) -> Order:
    """Update order status from webhook."""
    order = db.query(Order).filter(Order.stripe_checkout_session_id == stripe_checkout_session_id).first()
    if not order:
        raise ValueError("Order not found")
    
    order.status = status
    if customer_email:
        order.customer_email = customer_email
    
    db.commit()
    db.refresh(order)
    
    return order
