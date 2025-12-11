# reset_superadmin.py
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

MONGO_URL = "mongodb://localhost:27017"  # replace if different
DB_NAME = "master_db"                     # replace with your DB name
ADMIN_EMAIL = "superadmin@example.com"    # the admin you want to reset
NEW_PASSWORD = "MyNewPass123"             # new password you want to set

async def reset_superadmin_password():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    hashed = bcrypt.hashpw(NEW_PASSWORD.encode(), bcrypt.gensalt()).decode()

    result = await db.admins.update_one(
        {"email": ADMIN_EMAIL},
        {"$set": {"hashed_password": hashed}}
    )

    if result.modified_count:
        print(f"✅ Password reset successful for {ADMIN_EMAIL}")
    else:
        print(f"⚠️ Admin {ADMIN_EMAIL} not found or password unchanged")

    client.close()

if __name__ == "__main__":
    asyncio.run(reset_superadmin_password())
