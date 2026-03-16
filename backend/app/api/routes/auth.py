import asyncio
from fastapi import APIRouter, HTTPException, status, Depends
from app.models import UserSignUp, UserSignIn, AuthResponse, ProfileResponse, ProfileUpdate
from app.core.security import create_access_token
from app.core.dependencies import get_current_user
from app.db.supabase_client import get_supabase_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignUp):
    supabase = get_supabase_client()
    
    try:
        auth_response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {"full_name": payload.full_name}
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed — user not created"
            )
        
        user = auth_response.user
        access_token = create_access_token(data={"sub": str(user.id)})
        
        # Wait briefly for trigger to fire
        await asyncio.sleep(0.5)
        
        profile_result = supabase.table("profiles")\
            .select("*")\
            .eq("id", str(user.id))\
            .single()\
            .execute()
        
        # Fallback if trigger didn't fire in time
        if not profile_result.data:
            supabase.table("profiles").insert({
                "id": str(user.id),
                "email": payload.email,
                "full_name": payload.full_name
            }).execute()
            
            profile_result = supabase.table("profiles")\
                .select("*")\
                .eq("id", str(user.id))\
                .single()\
                .execute()
        
        logger.info(f"New user signed up: {payload.email}")
        
        return AuthResponse(
            access_token=access_token,
            user=ProfileResponse(**profile_result.data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: UserSignIn):
    supabase = get_supabase_client()
    
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = auth_response.user
        access_token = create_access_token(data={"sub": str(user.id)})
        
        profile_result = supabase.table("profiles")\
            .select("*")\
            .eq("id", str(user.id))\
            .single()\
            .execute()
        
        logger.info(f"User signed in: {payload.email}")
        
        return AuthResponse(
            access_token=access_token,
            user=ProfileResponse(**profile_result.data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/signout")
async def signout(current_user: ProfileResponse = Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
        logger.info(f"User signed out: {current_user.email}")
        return {"message": "Signed out successfully"}
    except Exception as e:
        logger.error(f"Signout error: {e}")
        return {"message": "Signed out"}


@router.get("/me", response_model=ProfileResponse)
async def get_me(current_user: ProfileResponse = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate,
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    try:
        update_data = payload.model_dump(exclude_none=True)
        
        if not update_data:
            return current_user
        
        result = supabase.table("profiles")\
            .update(update_data)\
            .eq("id", str(current_user.id))\
            .execute()
        
        logger.info(f"Profile updated for user: {current_user.email}")
        return ProfileResponse(**result.data[0])
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )