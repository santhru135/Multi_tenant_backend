"""
Organization service for managing multi-tenant organizations.
Handles organization CRUD operations with admin user management.
"""
from typing import Dict, Optional, Any
import logging
from datetime import datetime
from bson import ObjectId

from db.master_db import get_master_db, get_database
from models.organization import OrganizationModel, OrgCreateRequest, OrgUpdateRequest, OrgResponse, OrganizationStatus
from models.user import AdminUserInDB, AdminUserCreate
from auth.password_handler import get_password_hash

logger = logging.getLogger(__name__)

class OrganizationService:
    def __init__(self):
        """Initialize the OrganizationService with database connections."""
        self.master_db = get_master_db()
        self.organizations = self.master_db.organizations
        self.admin_users = self.master_db.admin_users

    async def _get_collection_name(self, org_name: str) -> str:
        """Generate collection name for an organization."""
        return f"org_{org_name.lower().replace(' ', '_')}"

    async def create_organization(
        self, 
        organization_name: str, 
        admin_email: str, 
        admin_password: str
    ) -> Dict:
        """
        Create a new organization with an admin user.
        
        Args:
            organization_name: Name of the organization
            admin_email: Admin user's email
            admin_password: Admin user's password
            
        Returns:
            Created organization details
        """
        try:
            # Check if organization already exists
            if await self.get_organization(organization_name):
                raise ValueError(f"Organization '{organization_name}' already exists")

            # Create organization document
            org_data = {
                "name": organization_name,
                "name_lower": organization_name.lower(),
                "status": "active",
                "created_at": datetime.utcnow(),
                "metadata": {}
            }
            
            # Save to database
            result = await self.organizations.insert_one(org_data)
            org_data["id"] = str(result.inserted_id)
            
            # Invalidate cache
            await self._invalidate_org_cache(organization_name)
            
            return org_data
            
        except Exception as e:
            logger.error(f"Error creating organization {organization_name}: {str(e)}")
            raise

    async def update_organization(
        self, 
        organization_name: str, 
        new_name: str
    ) -> Dict:
        """
        Update an organization's name.
        
        Args:
            organization_name: Current organization name
            new_name: New organization name
            
        Returns:
            Updated organization details
        """
        try:
            # Update organization in database
            result = await self.organizations.update_one(
                {"name_lower": organization_name.lower()},
                {"$set": {
                    "name": new_name,
                    "name_lower": new_name.lower()
                }}
            )
            
            if result.modified_count == 0:
                raise ValueError(f"Organization '{organization_name}' not found")
                
            # Invalidate cache for both old and new names
            await self._invalidate_org_cache(organization_name)
            await self._invalidate_org_cache(new_name)
            
            return await self.get_organization(new_name)
            
        except Exception as e:
            logger.error(f"Error updating organization {organization_name}: {str(e)}")
            raise

    async def delete_organization(self, organization_name: str) -> bool:
        """
        Delete an organization.
        
        Args:
            organization_name: Name of the organization to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # Delete from database
            result = await self.organizations.delete_one(
                {"name_lower": organization_name.lower()}
            )
            
            if result.deleted_count == 0:
                raise ValueError(f"Organization '{organization_name}' not found")
                
            # Invalidate cache
            await self._invalidate_org_cache(organization_name)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting organization {organization_name}: {str(e)}")
            raise

    async def _invalidate_org_cache(self, organization_name: str):
        """Invalidate organization cache if Redis is available."""
        try:
            await delete_cached_data(f"org:{organization_name}")
        except Exception as e:
            # Log but don't fail the operation if cache invalidation fails
            logger.warning(f"Could not invalidate cache for org {organization_name}: {e}")
            logger.info("Application will continue without cache invalidation")