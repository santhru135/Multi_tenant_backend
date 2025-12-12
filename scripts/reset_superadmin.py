# scripts/reset_superadmin.py
import asyncio
from db.master_db import connect_master_db, close_master_db, get_database
from auth.password_handler import get_password_hash
from config.settings import settings

SUPERADMIN_EMAIL = "superadmin@example.com"
SUPERADMIN_PASSWORD = "NewSecurePassword123"
SUPERADMIN_ORG = "system"

async def reset_superadmin():
    # Connect to Master DB (await because it's async)
    await connect_master_db()

    # Get the database after connection
    db = get_database(settings.MASTER_DB_NAME)

    # Check if superadmin exists
    superadmin = await db.admins.find_one({"email": SUPERADMIN_EMAIL})

    if superadmin:
        print("Superadmin exists. Resetting password...")
        hashed_password = get_password_hash(SUPERADMIN_PASSWORD)
        await db.admins.update_one(
            {"email": SUPERADMIN_EMAIL},
            {"$set": {"hashed_password": hashed_password}}
        )
        print("Password reset successfully.")
    else:
        print("Superadmin does not exist. Creating...")
        hashed_password = get_password_hash(SUPERADMIN_PASSWORD)
        await db.admins.insert_one({
            "email": SUPERADMIN_EMAIL,
            "hashed_password": hashed_password,
            "org_name": SUPERADMIN_ORG,
            "is_superadmin": True,
            "is_active": True
        })
        print("Superadmin created successfully.")

    # Close Master DB connection
    await close_master_db()

if __name__ == "__main__":
    asyncio.run(reset_superadmin())
