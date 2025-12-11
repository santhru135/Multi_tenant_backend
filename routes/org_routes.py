# routes/org_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from models.organization import OrgCreateRequest
from services.org_service import OrganizationService
from auth.jwt_handler import get_current_org_admin

router = APIRouter(prefix="/org", tags=["organizations"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrgCreateRequest,
    current_admin: dict = Depends(get_current_org_admin)
):
    # Only superadmins can create organizations
    if not current_admin.is_superadmin:
        raise HTTPException(status_code=403, detail="Only superadmins can create organizations")

    org_service = OrganizationService()
    try:
        result = await org_service.create_organization(org_data)
        return {"status": "success", "message": "Organization created", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get")
async def get_organization(organization_name: str):
    org_service = OrganizationService()
    org = await org_service.get_organization(organization_name)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/update")
async def update_organization(old_name: str, new_name: str):
    org_service = OrganizationService()
    updated_count = await org_service.update_organization(old_name, new_name)
    if updated_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "success", "message": "Organization updated"}


@router.delete("/delete")
async def delete_organization(organization_name: str):
    org_service = OrganizationService()
    deleted_count = await org_service.delete_organization(organization_name)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "success", "message": "Organization deleted"}
