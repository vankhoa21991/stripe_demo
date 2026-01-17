"""Order API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas import OrderResponse
from app.models import Order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get order by ID."""
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.get("/by-session/{session_id}", response_model=OrderResponse)
def get_order_by_session(session_id: str, db: Session = Depends(get_db)):
    """Get order by Stripe Checkout Session ID."""
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.stripe_checkout_session_id == session_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order
