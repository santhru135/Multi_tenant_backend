from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum
from .pyobjectid import PyObjectId
from bson import ObjectId

class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

# Request to create org
class OrgCreateRequest(BaseModel):
    organization_name: str = Field(..., min_length=3, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

# Request to update org name
class OrgUpdateRequest(BaseModel):
    old_name: str
    new_name: str = Field(..., min_length=3, max_length=100)

# Response model
class OrgResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    organization_name: str
    collection_name: str
    admin_id: PyObjectId
    status: OrganizationStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},  # avoids PydanticSerializationError
    }

# Internal DB model
class OrganizationModel(BaseModel):
    organization_name: str
    collection_name: str
    admin_id: PyObjectId
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
    }
