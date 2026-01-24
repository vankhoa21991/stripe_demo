"""Supabase client initialization."""
from supabase import create_client, Client
from app.config import settings

# Initialize Supabase client
supabase_client: Client = create_client(settings.supabase_url, settings.supabase_key)


def get_supabase() -> Client:
    """Dependency for getting Supabase client."""
    return supabase_client
