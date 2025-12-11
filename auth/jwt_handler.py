from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from config.settings import settings
from models.auth import TokenData

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES  # use config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/login")

def generate_org_admin_token(admin_id: str, org_name: str, is_superadmin: bool = False) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": admin_id,
        "org": org_name,
        "is_superadmin": is_superadmin,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_org_admin(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        org_name = payload.get("org")
        is_superadmin = payload.get("is_superadmin", False)

        if not admin_id or not org_name:
            raise credentials_exception

        return TokenData(
            admin_id=admin_id,
            organization=org_name,
            is_superadmin=is_superadmin
        )
    except JWTError:
        raise credentials_exception
