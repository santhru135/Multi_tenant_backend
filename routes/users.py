# routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from models.user import UserCreate, UserInDB, UserUpdate
from db.master_db import MasterDatabase
from auth.password_handler import get_password_hash, verify_password
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Create a new user
    - **email**: must be unique
    - **password**: will be hashed before storage
    - **organization_name**: must be a valid organization
    """
    db = await MasterDatabase.connect_db()
    
    # Check if user already exists
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Verify organization exists
    org = await db.organizations.find_one({"organization_name": user.organization_name})
    if not org:
        raise HTTPException(
            status_code=400,
            detail=f"Organization '{user.organization_name}' not found"
        )
    
    # Hash the password
    user_dict = user.dict()
    user_dict["password_hash"] = get_password_hash(user.password_hash)
    user_dict.pop("password_hash", None)  # Remove the plain password
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = user_dict["created_at"]
    user_dict["is_active"] = True
    
    # Insert user into database
    result = await db.users.insert_one(user_dict)
    
    # Return the created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    return created_user

@router.get("/{user_id}", response_model=UserInDB)
async def get_user(user_id: str):
    """
    Get user by ID
    - **user_id**: The ID of the user to retrieve
    """
    try:
        db = await MasterDatabase.connect_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user["_id"] = str(user["_id"])
        return user
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

@router.get("/", response_model=List[UserInDB])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, le=100, description="Maximum number of records to return"),
    organization_name: Optional[str] = Query(None, description="Filter by organization")
):
    """
    List users with pagination and optional filtering
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **organization_name**: Filter users by organization
    """
    db = await MasterDatabase.connect_db()
    
    # Build query
    query = {}
    if organization_name:
        query["organization_name"] = organization_name
    
    # Get users with pagination
    users = []
    async for user in db.users.find(query).skip(skip).limit(limit):
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return users

@router.patch("/{user_id}", response_model=UserInDB)
async def update_user(user_id: str, user_update: UserUpdate):
    """
    Update user details
    - Only provided fields will be updated
    - Password updates should use the change_password endpoint
    """
    db = await MasterDatabase.connect_db()
    
    # Get existing user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)
    
    # Don't allow updating password through this endpoint
    if 'password_hash' in update_data:
        del update_data['password_hash']
    
    # If there's nothing to update, return current user
    if not update_data:
        user["_id"] = str(user["_id"])
        return user
    
    # Update user
    update_data["updated_at"] = datetime.utcnow()
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Return updated user
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_user["_id"] = str(updated_user["_id"])
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """
    Delete a user
    - This is a soft delete (sets is_active to False)
    """
    db = await MasterDatabase.connect_db()
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return None

@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    user_id: str,
    current_password: str,
    new_password: str
):
    """
    Change user password
    - Requires current password for verification
    - New password must be different from current password
    """
    db = await MasterDatabase.connect_db()
    
    # Get user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Verify new password is different
    if verify_password(new_password, user["password_hash"]):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )
    
    # Update password
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_hash": get_password_hash(new_password),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Password updated successfully"}
