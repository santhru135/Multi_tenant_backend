from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from .pyobjectid import PyObjectId

class AdminUserBase(BaseModel):
    email: EmailStr
    hashed_password: str
    org_name: str
    is_superadmin: bool = False
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    org_name: str
    is_superadmin: bool = False

class AdminUserInDB(AdminUserBase):
    id: PyObjectId = Field(alias="_id")
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True

class AdminUserResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    org_name: str
    is_superadmin: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True