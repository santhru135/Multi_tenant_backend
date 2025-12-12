import asyncio
from db.master_db import connect_master_db, get_database

async def check():
    await connect_master_db()
    db = get_database("multi_tenant")

    print("ADMINS:", await db.admins.find_one({"is_superadmin": True}))
    print("ADMIN_USERS:", await db.admin_users.find_one({"is_superadmin": True}))

asyncio.run(check())
