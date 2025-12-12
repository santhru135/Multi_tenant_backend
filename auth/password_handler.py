# auth/password_handler.py
from passlib.context import CryptContext

# Create a password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hash a plain password.
    No truncation needed; passlib handles bcrypt limitations internally.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a stored hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)
