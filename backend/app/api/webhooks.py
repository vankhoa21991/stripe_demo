"""Stripe webhook handler."""
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe

from app.database import get_db
from app.config import settings
from app.models import StripeEvent
from app.services.order_service import update_order_status

router = APIRouter(prefix="/stripe", tags=["webhooks"])


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    
    # Check idempotency
    existing_event = db.query(StripeEvent).filter(
        StripeEvent.stripe_event_id == event.id
    ).first()
    
    if existing_event and existing_event.processed:
        # Already processed, return 200 (idempotent)
        return {"status": "already_processed"}
    
    # Store event
    if not existing_event:
        stripe_event = StripeEvent(
            stripe_event_id=event.id,
            event_type=event.type
        )
        db.add(stripe_event)
        db.commit()
        db.refresh(stripe_event)
    else:
        stripe_event = existing_event
    
    # Process event
    try:
        if event.type == "checkout.session.completed":
            session = event.data.object
            customer_email = session.customer_details.email if session.customer_details else None
            
            update_order_status(
                db,
                session.id,
                "paid",
                customer_email
            )
        
        stripe_event.processed = True
        from datetime import datetime
        stripe_event.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Log error but don't fail the webhook
        # Stripe will retry
        print(f"Error processing webhook event {event.id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")
    
    return {"status": "success"}
