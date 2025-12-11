# routes/__init__.py
"""
Routes package for the multi-tenant backend API.
"""

from .admin_routes import router as admin_router
from .org_routes import router as org_router

# List of all route modules
__all__ = ["admin_router", "org_router"]