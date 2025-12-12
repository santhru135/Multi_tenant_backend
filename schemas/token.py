from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    tenant_id: Optional[str] = None
    is_superadmin: bool = False
    scopes: list[str] = []

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []
    tenant_id: Optional[str] = None

class RefreshTokenCreate(BaseModel):
    token: str
    expires_at: datetime
    user_id: str
    tenant_id: str
    is_superadmin: bool = False

class RefreshTokenInDB(RefreshTokenCreate):
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TokenCreate(BaseModel):
    user_id: str
    tenant_id: str
    is_superadmin: bool = False
    expires_delta: Optional[timedelta] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user_id: str
    tenant_id: str
    is_superadmin: bool
    scopes: list[str] = []
