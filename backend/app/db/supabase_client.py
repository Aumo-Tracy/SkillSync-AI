from supabase import create_client, Client
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_supabase_client: Client | None = None
_supabase_admin_client: Client | None = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        logger.info("Supabase client initialized")
    return _supabase_client

def get_supabase_admin_client() -> Client:
    # Uses service role key — bypasses RLS
    # Only use this for admin operations, never expose to frontend
    global _supabase_admin_client
    if _supabase_admin_client is None:
        _supabase_admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        logger.info("Supabase admin client initialized")
    return _supabase_admin_client