from typing import Any, Optional
from fastapi import Request, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from contextvars import ContextVar
from core.config import settings

# Context variable to store the current tenant ID
tenant_id_ctx_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)

class DatabaseRouter:
    def __init__(self, master_db):
        self.master_db = master_db
        self._client = master_db.client
        self._tenant_dbs = {}
    
    async def get_tenant_db(self, tenant_id: str) -> AsyncIOMotorDatabase:
        """Get or create a database connection for a specific tenant."""
        if tenant_id not in self._tenant_dbs:
            # In a real app, you might want to validate the tenant_id exists
            # and get the specific connection details from a configuration
            db_name = f"tenant_{tenant_id}"
            self._tenant_dbs[tenant_id] = self._client[db_name]
        return self._tenant_dbs[tenant_id]
    
    async def get_current_db(self, request: Request) -> AsyncIOMotorDatabase:
        """Get the appropriate database based on the current request context."""
        # First try to get tenant_id from the JWT token
        tenant_id = request.state.tenant_id if hasattr(request.state, 'tenant_id') else None
        
        # If not in JWT, try to get from the path or header
        if not tenant_id:
            # Check for tenant in path (e.g., /api/tenant/{tenant_id}/resource)
            if 'tenant_id' in request.path_params:
                tenant_id = request.path_params['tenant_id']
            # Check for tenant in header
            elif 'X-Tenant-ID' in request.headers:
                tenant_id = request.headers['X-Tenant-ID']
        
        if not tenant_id:
            # If no tenant specified, use the master database
            return self.master_db
            
        return await self.get_tenant_db(tenant_id)

# Initialize the database router
db_router: Optional[DatabaseRouter] = None

def get_db_router() -> DatabaseRouter:
    if db_router is None:
        raise RuntimeError("Database router not initialized")
    return db_router

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    """Dependency to get the current database based on the request context."""
    router = get_db_router()
    return await router.get_current_db(request)
