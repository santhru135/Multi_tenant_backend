from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List

from models.tenant import TenantCreate, TenantUpdate, TenantResponse, TenantListResponse
from services.tenant_service import TenantService, get_tenant_service
from core.security import get_current_active_user, get_current_active_superuser
from models.user import AdminUserInDB

router = APIRouter()

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    tenant_service: TenantService = Depends(get_tenant_service),
    current_user: AdminUserInDB = Depends(get_current_active_superuser)
):
    """
    Create a new tenant (superadmin only).
    This will create a new tenant and an admin user for that tenant.
    """
    try:
        tenant = await tenant_service.create_tenant(tenant_data)
        return tenant
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the tenant"
        )

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service),
    current_user: AdminUserInDB = Depends(get_current_active_user)
):
    """
    Get tenant by ID.
    Superadmins can access any tenant, tenant admins can only access their own tenant.
    """
    if not current_user.is_superadmin and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this tenant"
        )
    
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    tenant_service: TenantService = Depends(get_tenant_service),
    current_user: AdminUserInDB = Depends(get_current_active_superuser)
):
    """
    Update a tenant (superadmin only).
    """
    try:
        updated_tenant = await tenant_service.update_tenant(tenant_id, tenant_data)
        if not updated_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        return updated_tenant
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the tenant"
        )

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service),
    current_user: AdminUserInDB = Depends(get_current_active_superuser)
):
    """
    Delete a tenant (superadmin only).
    This will also remove all data associated with this tenant.
    """
    success = await tenant_service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return None

@router.get("/", response_model=TenantListResponse)
async def list_tenants(
    skip: int = 0,
    limit: int = 10,
    tenant_service: TenantService = Depends(get_tenant_service),
    current_user: AdminUserInDB = Depends(get_current_active_superuser)
):
    """
    List all tenants (superadmin only).
    """
    tenants = await tenant_service.list_tenants(skip=skip, limit=limit)
    total = await tenant_service.tenants_collection.count_documents({})
    
    return {
        "items": tenants,
        "total": total,
        "page": skip // limit + 1,
        "size": limit
    }
