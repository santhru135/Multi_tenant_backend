# services/org_service.py
from db.master_db import get_master_db
from models.organization import OrgCreateRequest, OrganizationModel
from bson import ObjectId

class OrganizationService:
    def __init__(self):
        self.collection = get_master_db().get_collection("organizations")  # collection will be lazy-loaded

    @property
    def collection(self):
        if master_db is None:
            raise Exception("Master DB not connected yet")
        return master_db.get_collection("organizations")

    async def create_organization(self, org_data: OrgCreateRequest):
        # Prepare the document
        doc = {
            "organization_name": org_data.organization_name,
            "collection_name": org_data.organization_name.lower().replace(" ", "_"),
            "admin_id": ObjectId(),  # Assign a real admin ID here if available
            "status": "active",
            "created_at": org_data.dict().get("created_at")  # Optional
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_organization(self, organization_name: str):
        org = await self.collection.find_one({"organization_name": organization_name})
        if org:
            org["_id"] = str(org["_id"])
        return org

    async def update_organization(self, old_name: str, new_name: str):
        update_result = await self.collection.update_one(
            {"organization_name": old_name},
            {"$set": {"organization_name": new_name, "collection_name": new_name.lower().replace(" ", "_")}}
        )
        return update_result.modified_count

    async def delete_organization(self, organization_name: str):
        delete_result = await self.collection.delete_one({"organization_name": organization_name})
        return delete_result.deleted_count
