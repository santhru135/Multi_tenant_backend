from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Depends
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext
from pydantic import ValidationError

from core.config import settings
from core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from models.user import AdminUserInDB, AdminUserCreate, AdminUserResponse
from db.master_db import get_master_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db["admin_users"]

    async def authenticate_user(self, email: str, password: str) -> Optional[AdminUserInDB]:
        user = await self.users_collection.find_one({"email": email})
        if not user:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return AdminUserInDB(**user)

    async def create_user(self, user_data: AdminUserCreate) -> AdminUserInDB:
        # Check if user already exists
        existing_user = await self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user document
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["is_active"] = True
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        # Insert user into database
        result = await self.users_collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        
        return AdminUserInDB(**user_dict)

    async def create_tokens(self, user_id: str, is_superadmin: bool = False, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        access_token = create_access_token(
            subject=str(user_id),
            tenant_id=tenant_id,
            is_superadmin=is_superadmin
        )
        
        refresh_token = create_refresh_token(
            subject=str(user_id),
            tenant_id=tenant_id,
            is_superadmin=is_superadmin
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify this is a refresh token
            if not payload.get("refresh"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            is_superadmin = payload.get("is_superadmin", False)
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Verify user still exists and is active
            user = await self.users_collection.find_one({"_id": user_id})
            if not user or not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new tokens
            return await self.create_tokens(
                user_id=user_id,
                is_superadmin=is_superadmin,
                tenant_id=tenant_id
            )
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_master_db)) -> AuthService:
    return AuthService(db)
