# services/admin_service.py
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId

from db.master_db import get_master_db
from models.user import AdminUserInDB, AdminUserCreate
from auth.password_handler import verify_password, get_password_hash
from config.settings import settings

class AdminService:
    def __init__(self):
        self.db = get_master_db()
        self.admin_users = self.db.admins


    async def authenticate_admin(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        admin = await self.get_admin_by_email(email)
        if not admin:
            return None
        
        if not await verify_password(password, admin["hashed_password"]):
            return None

        return {
            "id": str(admin["_id"]),
            "email": admin["email"],
            "org_name": admin["org_name"],
            "is_superadmin": admin.get("is_superadmin", False)
        }

    async def create_admin(self, email: str, password: str, org_name: str, is_superadmin: bool = False) -> str:
        hashed_password = await get_password_hash(password)  # Added await here
        admin_data = {
            "email": email.lower(),
            "hashed_password": hashed_password,
            "org_name": org_name,
            "is_superadmin": is_superadmin,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await self.admin_users.insert_one(admin_data)
        return str(result.inserted_id)

    async def get_admin_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.admin_users.find_one({"email": email.lower()})

    async def get_admin_by_id(self, admin_id: str) -> Optional[Dict[str, Any]]:
        return await self.admin_users.find_one({"_id": ObjectId(admin_id)})