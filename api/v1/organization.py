from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from passlib.context import CryptContext
from db.master_db import get_master_db
from datetime import datetime

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create router
router = APIRouter()

# Pydantic models
class OrgCreate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class OrgUpdate(BaseModel):
    organization_name: str
    email: Optional[EmailStr]
    password: Optional[str]

class OrgOut(BaseModel):
    organization_name: str
    collection_name: str
    admin_email: str

# Endpoints
@router.post("/create", response_model=OrgOut, status_code=201)
async def create_organization(org: OrgCreate):
    master_db = get_master_db()
    
    # Check if organization already exists
    existing = await master_db.organizations.find_one({"organization_name": org.organization_name})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization already exists"
        )
    
    # Create collection name
    collection_name = f"org_{org.organization_name.lower().replace(' ', '_')}"
    
    # Hash password
    hashed_password = pwd_context.hash(org.password)
    
    # Create organization document
    org_doc = {
        "organization_name": org.organization_name,
        "collection_name": collection_name,
        "admin_email": org.email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    # Insert into database
    result = await master_db.organizations.insert_one(org_doc)
    
    return {
        "organization_name": org.organization_name,
        "collection_name": collection_name,
        "admin_email": org.email
    }

@router.get("/{organization_name}", response_model=OrgOut)
async def get_organization(organization_name: str):
    master_db = get_master_db()
    org = await master_db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return OrgOut(
        organization_name=org["organization_name"],
        collection_name=org["collection_name"],
        admin_email=org["admin_email"]
    )

@router.put("/{organization_name}", response_model=OrgOut)
async def update_organization(organization_name: str, org_update: OrgUpdate):
    master_db = get_master_db()
    
    org = await master_db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    update_data = {}
    if org_update.email:
        update_data["admin_email"] = org_update.email
    if org_update.password:
        update_data["hashed_password"] = pwd_context.hash(org_update.password)
    
    await master_db.organizations.update_one(
        {"organization_name": organization_name},
        {"$set": update_data}
    )
    
    updated_org = await master_db.organizations.find_one({"organization_name": organization_name})
    
    return OrgOut(
        organization_name=updated_org["organization_name"],
        collection_name=updated_org["collection_name"],
        admin_email=updated_org["admin_email"]
    )

@router.delete("/{organization_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(organization_name: str):
    master_db = get_master_db()
    
    org = await master_db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Drop the tenant collection
    await master_db.client.get_database()[org["collection_name"]].drop()
    
    # Remove from master DB
    await master_db.organizations.delete_one({"organization_name": organization_name})
    
    return None