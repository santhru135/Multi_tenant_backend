from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from core.config import settings
from core.security import create_access_token, create_refresh_token
from models.user import AdminUserCreate, AdminUserResponse
from schemas.token import Token, TokenResponse
from services.auth_service import AuthService, get_auth_service

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For now, we're not handling tenant-specific login here
    # In a real app, you'd determine the tenant from the request or user data
    tokens = await auth_service.create_tokens(
        user_id=str(user.id),
        is_superadmin=user.is_superadmin
    )
    
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer",
        "refresh_token": tokens["refresh_token"]
    }

@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        tokens = await auth_service.refresh_tokens(refresh_token)
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer",
            "refresh_token": tokens["refresh_token"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: AdminUserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        user = await auth_service.create_user(user_data)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )
