# db/master_db.py
import motor.motor_asyncio
from core.config import settings

_master_db = None

async def connect_master_db():
    global _master_db
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    _master_db = client[settings.MASTER_DB_NAME]
    print(f"Connected to Master DB: {settings.MASTER_DB_NAME}")

async def close_master_db():
    global _master_db
    _master_db.client.close()
    _master_db = None
    print("Closed Master DB connection")

def get_master_db():
    if not _master_db:
        raise Exception("Master DB not connected")
    return _master_db
