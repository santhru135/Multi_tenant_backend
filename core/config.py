import os
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Tenant Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MASTER_DB_NAME: str = os.getenv("MASTER_DB_NAME")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL") 
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
