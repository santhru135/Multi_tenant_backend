from fastapi import APIRouter, Depends, HTTPException, status
from models.organization import OrgCreateRequest, OrgUpdateRequest, OrgResponse
from services.org_service import OrganizationService
from auth.jwt_handler import get_current_org_admin

router = APIRouter(prefix="/org", tags=["organizations"])

@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrgCreateRequest,
    current_admin: dict = Depends(get_current_org_admin)
):
    org_service = OrganizationService()
    try:
        # Only superadmins can create new organizations
        if not current_admin.get("is_superadmin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmins can create organizations"
            )
            
        result = await org_service.create_organization(org_data)
        return {
            "status": "success",
            "message": "Organization created successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Update other routes similarly...