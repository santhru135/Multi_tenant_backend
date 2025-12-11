"""
Database utility functions and helpers.
Common database operations and connection management.
"""
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.results import UpdateResult, DeleteResult

def convert_objectid(data: Any) -> Any:
    """Convert ObjectId to string in a document or list of documents"""
    if isinstance(data, list):
        return [convert_objectid(item) for item in data]
    if isinstance(data, dict):
        if "_id" in data:
            data["id"] = str(data.pop("_id"))
        return {k: convert_objectid(v) for k, v in data.items()}
    return data

async def get_document(collection, query: dict, projection: dict = None) -> Optional[dict]:
    """Get a single document from a collection"""
    result = await collection.find_one(query, projection)
    return convert_objectid(result) if result else None

async def get_documents(
    collection,
    query: dict = None,
    projection: dict = None,
    skip: int = 0,
    limit: int = 100
) -> List[dict]:
    """Get multiple documents from a collection"""
    query = query or {}
    cursor = collection.find(query, projection).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    return convert_objectid(results)