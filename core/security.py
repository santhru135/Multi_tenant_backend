from datetime import datetime, timedelta
from typing import Any, Optional, Union
from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.config import settings
from models.user import AdminUserInDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    tenant_id: Optional[str] = None,
    is_superadmin: bool = False,
    scopes: Optional[list] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "is_superadmin": is_superadmin,
        "scopes": scopes or []
    }
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )

def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    tenant_id: Optional[str] = None,
    is_superadmin: bool = False
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "is_superadmin": is_superadmin,
        "refresh": True
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AdminUserInDB:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Here you would typically fetch the user from the database
        # user = await get_user(user_id)
        # if user is None:
        #     raise credentials_exception
        # return user
        
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # This is a placeholder - implement actual user retrieval
    return AdminUserInDB(
        id=user_id,
        email="user@example.com",  # Replace with actual user data
        hashed_password="",
        org_name="",
        is_superadmin=payload.get("is_superadmin", False)
    )

def get_current_active_user(
    current_user: AdminUserInDB = Depends(get_current_user),
) -> AdminUserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: AdminUserInDB = Depends(get_current_user),
) -> AdminUserInDB:
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=403, 
            detail="The user doesn't have enough privileges"
        )
    return current_user
