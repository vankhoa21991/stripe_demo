"""Supabase client initialization with retry logic and connection handling."""
import logging
from typing import Optional
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_client: Optional[Client] = None


def _create_supabase_client() -> Client:
    """Create a new Supabase client."""
    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        raise


def get_supabase() -> Client:
    """Dependency for getting Supabase client with lazy initialization."""
    global supabase_client
    
    if supabase_client is None:
        supabase_client = _create_supabase_client()
    
    return supabase_client


def reset_supabase_client():
    """Reset the Supabase client (useful for connection recovery)."""
    global supabase_client
    logger.warning("Resetting Supabase client")
    supabase_client = None
    supabase_client = _create_supabase_client()
