from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.auth import AdminLoginRequest, LoginResponse
from services.admin_service import AdminService
from auth.jwt_handler import generate_org_admin_token

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_service = AdminService()
    admin = await admin_service.authenticate_admin(form_data.username, form_data.password)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = generate_org_admin_token(
        admin_id=admin["id"],
        org_name=admin["org_name"],
        is_superadmin=admin.get("is_superadmin", False)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_id": admin["id"],
        "organization": admin["org_name"]
    }