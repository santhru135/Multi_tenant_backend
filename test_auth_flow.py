import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from models.user import AdminUserCreate
from services.auth_service import AuthService
from core.config import settings

async def test_auth_flow():
    print("🔍 Starting authentication flow test...")
    
    # Connect to MongoDB
    print("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MASTER_DB_NAME]
    auth_service = AuthService(db)

    # Test user data
    test_email = "testuser@example.com"
    test_password = "Test@1234"
    test_org = "Test Org"

    try:
        # Create a test user
        print(f"👤 Creating test user: {test_email}...")
        user_data = AdminUserCreate(
            email=test_email,
            password=test_password,
            org_name=test_org,
            is_superadmin=True
        )
        
        # Register the user
        user = await auth_service.create_user(user_data)
        print(f"✅ Created user: {user.email}")

        # Authenticate the user
        print("🔐 Attempting to authenticate...")
        auth_user = await auth_service.authenticate_user(test_email, test_password)
        if auth_user:
            print("✅ Login successful!")
            print(f"   User ID: {auth_user.id}")
            print(f"   Is Superadmin: {auth_user.is_superadmin}")
            
            # Test token creation
            print("🔑 Testing token creation...")
            tokens = await auth_service.create_tokens(
                user_id=str(auth_user.id),
                is_superadmin=auth_user.is_superadmin
            )
            print(f"   Access token: {tokens['access_token'][:50]}...")
            print(f"   Refresh token: {tokens['refresh_token'][:50]}...")
        else:
            print("❌ Login failed - invalid credentials")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up - remove test user
        print("🧹 Cleaning up test user...")
        await db["admin_users"].delete_one({"email": test_email})
        print("✅ Test completed and cleaned up")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_auth_flow())
