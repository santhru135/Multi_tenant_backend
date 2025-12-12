from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from models.tenant import TenantCreate, TenantUpdate, TenantInDB, TenantResponse
from models.user import AdminUserInDB, AdminUserCreate, AdminUserResponse
from db.master_db import get_master_db
from services.auth_service import AuthService
from core.security import get_password_hash

class TenantService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.tenants_collection = db["tenants"]
        self.auth_service = AuthService(db)

    async def create_tenant(self, tenant_data: TenantCreate) -> TenantInDB:
        # Check if tenant with this domain already exists
        existing_tenant = await self.tenants_collection.find_one({"domain": tenant_data.domain})
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with domain '{tenant_data.domain}' already exists"
            )
        
        # Create admin user first
        admin_user = await self._create_tenant_admin(
            email=tenant_data.admin_email,
            password=tenant_data.admin_password,
            name=tenant_data.admin_name,
            is_superadmin=False
        )
        
        # Create tenant document
        tenant_dict = tenant_data.dict(exclude={"admin_email", "admin_password", "admin_name"})
        tenant_dict["admin_id"] = admin_user.id
        tenant_dict["is_active"] = True
        tenant_dict["created_at"] = datetime.utcnow()
        tenant_dict["updated_at"] = datetime.utcnow()
        
        # Insert tenant into database
        result = await self.tenants_collection.insert_one(tenant_dict)
        tenant_dict["_id"] = result.inserted_id
        
        # Create the tenant database
        await self._create_tenant_database(str(result.inserted_id))
        
        return TenantInDB(**tenant_dict)

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[TenantInDB]:
        tenant = await self.tenants_collection.find_one({"_id": tenant_id})
        if not tenant:
            return None
        return TenantInDB(**tenant)

    async def get_tenant_by_domain(self, domain: str) -> Optional[TenantInDB]:
        tenant = await self.tenants_collection.find_one({"domain": domain})
        if not tenant:
            return None
        return TenantInDB(**tenant)

    async def update_tenant(
        self, tenant_id: str, update_data: TenantUpdate
    ) -> Optional[TenantInDB]:
        update_data_dict = update_data.dict(exclude_unset=True)
        update_data_dict["updated_at"] = datetime.utcnow()
        
        updated_tenant = await self.tenants_collection.find_one_and_update(
            {"_id": tenant_id},
            {"$set": update_data_dict},
            return_document=ReturnDocument.AFTER
        )
        
        if not updated_tenant:
            return None
            
        return TenantInDB(**updated_tenant)

    async def delete_tenant(self, tenant_id: str) -> bool:
        result = await self.tenants_collection.delete_one({"_id": tenant_id})
        return result.deleted_count > 0

    async def list_tenants(
        self, skip: int = 0, limit: int = 10
    ) -> List[TenantInDB]:
        cursor = self.tenants_collection.find().skip(skip).limit(limit)
        return [TenantInDB(**tenant) async for tenant in cursor]

    async def _create_tenant_admin(
        self, email: str, password: str, name: str, is_superadmin: bool = False
    ) -> AdminUserInDB:
        # Create admin user
        user_data = AdminUserCreate(
            email=email,
            password=password,
            full_name=name,
            is_superadmin=is_superadmin
        )
        return await self.auth_service.create_user(user_data)

    async def _create_tenant_database(self, tenant_id: str) -> None:
        # In a real implementation, this would create a new database for the tenant
        # For MongoDB, we don't need to explicitly create the database
        # It will be created when we first insert data into it
        pass

def get_tenant_service(db: AsyncIOMotorDatabase = Depends(get_master_db)) -> TenantService:
    return TenantService(db)
