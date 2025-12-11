from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config.settings import settings
from models.auth import TokenData

# JWT Configuration
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/login")

def generate_org_admin_token(admin_id: str, org_name: str, is_superadmin: bool = False) -> str:
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": admin_id,
        "org": org_name,
        "is_superadmin": is_superadmin,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_org_admin(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        org_name: str = payload.get("org")
        is_superadmin: bool = payload.get("is_superadmin", False)
        
        if admin_id is None or org_name is None:
            raise credentials_exception
            
        return TokenData(
            admin_id=admin_id,
            organization=org_name,
            is_superadmin=is_superadmin
        )
    except JWTError:
        raise credentials_exception

async def get_current_active_admin(current_admin: TokenData = Depends(get_current_org_admin)):
    return current_admin