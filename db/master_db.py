from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

# Initialize the MongoDB client
client = None
master_db = None

def get_master_db():
    """Get the master database instance."""
    global master_db
    if master_db is None:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        master_db = client[settings.DATABASE_NAME]
    return master_db

def get_database():
    """Get the database instance for the current tenant."""
    # In a real implementation, you would get the current tenant from the request
    # For now, we'll just return the master database
    return get_master_db()

async def close_connection():
    """Close the MongoDB connection."""
    global client
    if client:
        client.close()
        client = None