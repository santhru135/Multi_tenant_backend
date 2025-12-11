"""
Authentication routes for the FastAPI application.
Handles user registration, login, token management, and password reset functionality.
"""
from datetime import datetime, timedelta
import logging
import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from bson import ObjectId

from models.auth import Token, UserCreate, UserResponse, PasswordResetRequest, PasswordResetConfirm, RefreshToken
from models.user import UserInDB
from auth.jwt_handler import create_access_token, create_refresh_token, get_current_user, get_current_active_user, JWTBearer
from auth.password_handler import get_password_hash, verify_password, generate_temporary_password
from db.master_db import MasterDatabase
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user with the provided information.
    
    Args:
        user_data: User registration data including email and password
        
    Returns:
        UserResponse: The created user's information
        
    Raises:
        HTTPException: If email is already registered or validation fails
    """
    # Check if user already exists
    db = await MasterDatabase.connect_db()
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user_dict = user_data.dict(exclude={"password"})
    user_dict["password_hash"] = get_password_hash(user_data.password)
    user_dict["email"] = user_dict["email"].lower()
    user_dict["is_active"] = True
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    # Set default role if not provided
    if "roles" not in user_dict or not user_dict["roles"]:
        user_dict["roles"] = ["user"]

    # Insert user into database
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)

    # Convert to response model
    return UserResponse(**user_dict)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and return access and refresh tokens.
    
    Args:
        form_data: OAuth2 form data containing username (email) and password
        
    Returns:
        Token: Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    db = await MasterDatabase.connect_db()
    user = await db.users.find_one({"email": form_data.username.lower()})
    
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        # Update failed login attempts
        if user:
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$inc": {"login_attempts": 1}}
            )
            
            # Lock account after 5 failed attempts for 15 minutes
            if user.get("login_attempts", 0) >= 4:  # 0-based index
                lock_until = datetime.utcnow() + timedelta(minutes=15)
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"account_locked_until": lock_until}}
                )
                
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.get("account_locked_until") and user["account_locked_until"] > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked due to too many failed login attempts"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Update last login time and reset failed attempts
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "last_login": datetime.utcnow(),
                "login_attempts": 0,
                "account_locked_until": None
            }
        }
    )

    # Create tokens
    access_token_expires = timedelta(minutes=30)
    access_token = await create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=7)
    refresh_token = await create_refresh_token(
        user_id=str(user["_id"]),
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.seconds,
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: RefreshToken):
    """
    Refresh an access token using a valid refresh token.
    
    Args:
        refresh_token: The refresh token
        
    Returns:
        Token: New access token
        
    Raises:
        HTTPException: If refresh token is invalid or user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = await verify_token(refresh_token.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise credentials_exception
            
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
            
        # Verify user exists and is active
        db = await MasterDatabase.connect_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("is_active", True):
            raise credentials_exception
            
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        access_token = await create_access_token(
            data={"sub": str(user["_id"])},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.seconds
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise credentials_exception

@router.post("/password-reset-request")
async def request_password_reset(request_data: PasswordResetRequest, request: Request):
    """
    Request a password reset for a user's account.
    
    Args:
        request_data: Email address for password reset
        
    Returns:
        dict: Success message
    """
    db = await MasterDatabase.connect_db()
    user = await db.users.find_one({"email": request_data.email.lower()})
    
    if user:
        # Generate reset token (valid for 1 hour)
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token in database
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": reset_token_expires
                }
            }
        )
        
        # In a real application, send an email with the reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        # Log the reset link (in production, send email instead)
        logger.info(f"Password reset link for {user['email']}: {reset_link}")
        
        # TODO: Uncomment and implement email sending
        # await send_password_reset_email(
        #     email=user['email'],
        #     reset_link=reset_link,
        #     user_name=user.get('full_name', 'User')
        # )
    
    # Always return success to prevent user enumeration
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/password-reset")
async def reset_password(reset_data: PasswordResetConfirm):
    """
    Reset a user's password using a valid reset token.
    
    Args:
        reset_data: New password and reset token
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If reset token is invalid or expired
    """
    db = await MasterDatabase.connect_db()
    user = await db.users.find_one({
        "reset_token": reset_data.token,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password and clear reset token
    password_hash = get_password_hash(reset_data.new_password)
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": password_hash},
            "$unset": {"reset_token": "", "reset_token_expires": ""}
        }
    )
    
    return {"message": "Password updated successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get the current authenticated user's information.
    
    Args:
        current_user: The currently authenticated user
        
    Returns:
        UserResponse: The user's information
    """
    return current_user

@router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Change the current user's password.
    
    Args:
        current_password: The user's current password
        new_password: The new password
        current_user: The currently authenticated user
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    db = await MasterDatabase.connect_db()
    user = await db.users.find_one({"_id": ObjectId(current_user.id)})
    
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    password_hash = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"password_hash": password_hash, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Password updated successfully"}

@router.post("/logout")
async def logout(
    token: str = Depends(JWTBearer()),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Logout the current user.
    
    Note: In a production environment, you would want to implement token blacklisting.
    
    Args:
        token: The JWT token to invalidate
        current_user: The currently authenticated user
        
    Returns:
        dict: Success message
    """
    # In a production environment, you would add the token to a blacklist
    # For now, we'll just return success
    return {"message": "Successfully logged out"}
