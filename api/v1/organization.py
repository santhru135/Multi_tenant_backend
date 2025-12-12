from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from db.master_db import get_master_db
from datetime import datetime
from core.security import get_current_active_user
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# Response models
class OrgCreate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class OrgUpdate(BaseModel):
    organization_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

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
    
    # Create the organization's collection
    await master_db.create_collection(collection_name)
    
    return {
        "organization_name": org.organization_name,
        "collection_name": collection_name,
        "admin_email": org.email
    }

@router.get("/get", response_model=OrgOut)
async def get_organization(organization_name: str):
    master_db = get_master_db()
    org = await master_db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return {
        "organization_name": org["organization_name"],
        "collection_name": org["collection_name"],
        "admin_email": org["admin_email"]
    }

@router.put("/update", response_model=OrgOut)
async def update_organization(
    organization_name: str,
    new_org: OrgUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    master_db = get_master_db()
    
    # Check if organization exists
    org = await master_db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Verify current user is the admin of this organization
    if current_user["email"] != org["admin_email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this organization"
        )
    
    update_data = {}
    if new_org.email:
        update_data["admin_email"] = new_org.email
    if new_org.password:
        update_data["hashed_password"] = pwd_context.hash(new_org.password)
    
    # If organization name is being changed
    if new_org.organization_name and new_org.organization_name != organization_name:
        # Check if new name is taken
        existing = await master_db.organizations.find_one({"organization_name": new_org.organization_name})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already taken"
            )
        
        # Create new collection name
        new_collection_name = f"org_{new_org.organization_name.lower().replace(' ', '_')}"
        old_collection_name = org["collection_name"]
        
        # Rename the collection
        await master_db[old_collection_name].rename(new_collection_name)
        
        update_data.update({
            "organization_name": new_org.organization_name,
            "collection_name": new_collection_name
        })
    
    # Update organization document
    await master_db.organizations.update_one(
        {"organization_name": organization_name},
        {"$set": update_data}
    )
    
    # Get updated organization
    updated_org = await master_db.organizations.find_one(
        {"organization_name": new_org.organization_name or organization_name}
    )
    
    return {
        "organization_name": updated_org["organization_name"],
        "collection_name": updated_org["collection_name"],
        "admin_email": updated_org["admin_email"]
    }

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_name: str,
    current_user: dict = Depends(get_current_active_user)
):
    master_db = get_master_db()
    
    # Get organization
    org = await master_db.organizations.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Verify current user is the admin of this organization
    if current_user["email"] != org["admin_email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this organization"
        )
    
    # Drop the organization's collection
    await master_db.drop_collection(org["collection_name"])
    
    # Delete organization document
    await master_db.organizations.delete_one({"organization_name": organization_name})
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)