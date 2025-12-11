from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
from .pyobjectid import PyObjectId

class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class OrgCreateRequest(BaseModel):
    organization_name: str = Field(..., min_length=3, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

class OrgUpdateRequest(BaseModel):
    old_name: str
    new_name: str = Field(..., min_length=3, max_length=100)

    class Config:
        arbitrary_types_allowed = True

class OrgResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    organization_name: str
    collection_name: str
    admin_id: PyObjectId
    status: OrganizationStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True

class OrganizationModel(BaseModel):
    organization_name: str
    collection_name: str
    admin_id: PyObjectId
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True