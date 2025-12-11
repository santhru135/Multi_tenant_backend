from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from .pyobjectid import PyObjectId

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: str
    organization: str

class TokenData(BaseModel):
    admin_id: str
    organization: str | None = None
    is_superadmin: bool = False