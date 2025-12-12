from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# Global variables
_client = None
_master_db = None

async def connect_master_db():
    global _client, _master_db
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _master_db = _client[settings.MASTER_DB_NAME]
    return _master_db

async def close_master_db():
    if _client:
        _client.close()

def get_master_db():
    if _master_db is None:
        raise RuntimeError("Database not connected. Call connect_master_db() first.")
    return _master_db

# Add this function to resolve the import error
def get_database():
    return get_master_db()