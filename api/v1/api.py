from fastapi import APIRouter
from .organization import router as org_router
from .endpoints.auth import router as auth_router

# Create router with /api/v1 prefix
api_router = APIRouter()

# Include the organization router under /org
api_router.include_router(org_router, prefix="/org", tags=["Organization"])

# Include the auth router under /auth
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])