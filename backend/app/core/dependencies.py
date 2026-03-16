from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.db.supabase_client import get_supabase_client
from app.models import ProfileResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Tells FastAPI to expect Bearer token in Authorization header
bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> ProfileResponse:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode the JWT
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Fetch fresh profile from Supabase
    try:
        supabase = get_supabase_client()
        result = supabase.table("profiles")\
            .select("*")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise credentials_exception
            
        return ProfileResponse(**result.data)
        
    except Exception as e:
        logger.error(f"Failed to fetch user profile: {e}")
        raise credentials_exception

# Convenience alias — routes just declare Depends(get_current_user)
CurrentUser = Depends(get_current_user)