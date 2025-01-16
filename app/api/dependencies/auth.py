from typing import Annotated, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.supabase import supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise credentials_exception
            
        # Get user data from Supabase database
        response = supabase.table('users').select("*").eq('id', user.user.id).execute()
        if not response.data:
            raise credentials_exception
            
        return response.data[0]
    except APIError:
        raise credentials_exception

async def get_current_active_user(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)]
) -> Dict[str, Any]:
    if not current_user.get('is_active', False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)]
) -> Dict[str, Any]:
    if not current_user.get('is_superuser', False):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
