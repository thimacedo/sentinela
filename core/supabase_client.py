import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Return a Supabase client configured with env vars.
    Uses SUPABASE_URL and SUPABASE_SERVICE_KEY from .env.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase URL ou Service Key não configurados no .env")
    return create_client(url, key)
