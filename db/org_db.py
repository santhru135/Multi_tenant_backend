# db/org_db.py
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Dict, Any, Optional
from bson import ObjectId
import datetime

class OrgDatabase:
    def __init__(self, db, org_name: str):
        """Initialize organization database with specific organization collection."""
        self.collection = db[f"org_{org_name.lower()}"]

    async def insert_document(self, document: Dict[str, Any]) -> str:
        """Insert a single document into the organization's collection."""
        document["created_at"] = datetime.datetime.utcnow()
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        document = await self.collection.find_one({"_id": ObjectId(document_id)})
        if document:
            document["_id"] = str(document["_id"])
        return document

    async def update_document(
        self, document_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update a document in the collection."""
        update_data["updated_at"] = datetime.datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the collection."""
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0

    async def find_documents(
        self, query: Dict[str, Any] = None, limit: int = 100, skip: int = 0
    ) -> list:
        """Find multiple documents with optional query, limit, and skip."""
        if query is None:
            query = {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        documents = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents