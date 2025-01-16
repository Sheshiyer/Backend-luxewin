from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from postgrest.exceptions import APIError

from app.core.supabase import supabase
from app.models.schemas.user import UserCreate, Token, User as UserSchema
from app.services.notifications import notification_service
from app.services.notification_templates import NotificationTemplate

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    try:
        response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        return {"access_token": response.session.access_token}
    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=UserSchema)
async def register(user_in: UserCreate) -> Dict[str, Any]:
    try:
        # Register user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_in.email,
            "password": user_in.password
        })
        
        # Store additional user data in Supabase database
        user_data = {
            "id": auth_response.user.id,
            "email": user_in.email,
            "full_name": user_in.full_name,
            "wallet_address": user_in.wallet_address,
            "is_active": True,
            "is_superuser": False
        }
        
        data = supabase.table('users').insert(user_data).execute()
        
        # Register user in Novu and send welcome notification
        await notification_service.register_subscriber(
            subscriber_id=auth_response.user.id,
            email=user_in.email,
            full_name=user_in.full_name
        )
        await notification_service.trigger_event(
            name=NotificationTemplate.WELCOME,
            subscriber_id=auth_response.user.id,
            payload={"full_name": user_in.full_name}
        )
        
        return data.data[0]
    except APIError as e:
        if "already registered" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
