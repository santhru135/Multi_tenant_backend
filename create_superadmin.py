# create_superadmin.py
import asyncio
import sys
from services.admin_service import AdminService
from db.master_db import get_master_db, close_connection

async def create_superadmin():
    try:
        # Initialize database connection
        db = get_master_db()
        
        # Create admin service
        admin_service = AdminService()
        
        # Check if superadmin already exists
        existing = await admin_service.get_admin_by_email("superadmin@example.com")
        if existing:
            print("Superadmin already exists!")
            return
        
        # Create superadmin with a secure password
        admin_id = await admin_service.create_admin(
            email="superadmin@example.com",
            password="Admin@123",  # Shorter, secure password
            org_name="system",
            is_superadmin=True
        )
        print("✅ Superadmin created successfully!")
        print(f"Email: superadmin@example.com")
        print(f"Password: Admin@123")
    except Exception as e:
        print(f"❌ Error creating superadmin: {str(e)}")
        raise
    finally:
        # Close database connection
        await close_connection()

if __name__ == "__main__":
    asyncio.run(create_superadmin())