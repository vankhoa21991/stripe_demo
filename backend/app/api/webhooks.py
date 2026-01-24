"""Stripe webhook handler."""
from fastapi import APIRouter, Request, HTTPException, Depends
from supabase import Client
import stripe

from app.database import get_supabase
from app.config import settings
from app.services.order_service import update_order_status

router = APIRouter(prefix="/stripe", tags=["webhooks"])


@router.post("/webhook")
async def stripe_webhook(request: Request, supabase: Client = Depends(get_supabase)):
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
    result = supabase.table("stripe_events").select("*").eq("stripe_event_id", event.id).execute()
    existing_event = result.data[0] if result.data else None
    
    if existing_event and existing_event.get("processed"):
        # Already processed, return 200 (idempotent)
        return {"status": "already_processed"}
    
    # Store event
    if not existing_event:
        event_data = {
            "stripe_event_id": event.id,
            "event_type": event.type
        }
        result = supabase.table("stripe_events").insert(event_data).execute()
        stripe_event = result.data[0] if result.data else None
    else:
        stripe_event = existing_event
    
    # Process event
    try:
        if event.type == "checkout.session.completed":
            session = event.data.object
            customer_email = session.customer_details.email if session.customer_details else None
            
            update_order_status(
                supabase,
                session.id,
                "paid",
                customer_email
            )
        
        # Mark event as processed
        from datetime import datetime
        supabase.table("stripe_events").update({
            "processed": True,
            "processed_at": datetime.utcnow().isoformat()
        }).eq("id", stripe_event["id"]).execute()
        
    except Exception as e:
        # Log error but don't fail the webhook
        # Stripe will retry
        print(f"Error processing webhook event {event.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")
    
    return {"status": "success"}
