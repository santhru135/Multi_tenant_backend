from fastapi import APIRouter
from .organization import router as org_router

# Create router without any prefix
api_router = APIRouter()

# Include the organization router
api_router.include_router(org_router, tags=["Organization"])