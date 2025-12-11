# db/master_db.py
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

master_db_client = None
master_db = None

async def connect_master_db():
    global master_db_client, master_db
    master_db_client = AsyncIOMotorClient(settings.MONGODB_URL)
    master_db = master_db_client[settings.MASTER_DB_NAME]
    print("✅ Connected to Master MongoDB")

async def close_master_db():
    global master_db_client
    if master_db_client:
        master_db_client.close()
        print("✅ Closed Master MongoDB connection")

def get_master_db():
    if master_db is None:
        raise Exception("Master DB not connected yet")
    return master_db

def get_database(db_name: str):
    """Get any database by name using the master client."""
    if master_db_client is None:
        raise Exception("Master DB client not connected yet")
    return master_db_client[db_name]
