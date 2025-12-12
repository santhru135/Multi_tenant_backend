from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from .base import BaseDBModel, PyObjectId
from .user import AdminUserResponse

class TenantBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    domain: str = Field(..., min_length=3, max_length=63, pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$')
    email: EmailStr
    is_active: bool = True
    settings: Dict[str, Any] = {}
    admin_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TenantCreate(TenantBase):
    admin_name: str
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TenantInDB(TenantBase, BaseDBModel):
    pass

class TenantResponse(TenantBase):
    id: PyObjectId = Field(..., alias="_id")
    admin: Optional[AdminUserResponse] = None

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True

class TenantListResponse(BaseModel):
    items: List[TenantResponse]
    total: int
    page: int
    size: int
