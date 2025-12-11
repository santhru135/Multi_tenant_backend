# auth/password_handler.py
from passlib.context import CryptContext
from config.settings import settings

# Create password context with a default of 12 rounds if not set
bcrypt_rounds = getattr(settings, "BCRYPT_ROUNDS", 12)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=bcrypt_rounds,
    bcrypt__ident="2b"  # Explicitly use bcrypt 2b format
)

def truncate_password(password: str) -> str:
    """Truncate password to 72 bytes to avoid bcrypt limitation."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return password[:72].decode('latin-1')

async def get_password_hash(password: str) -> str:
    """Generate a hashed password."""
    truncated = truncate_password(password)
    return pwd_context.hash(truncated)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    truncated = truncate_password(plain_password)
    return pwd_context.verify(truncated, hashed_password)