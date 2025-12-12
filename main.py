import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from core.config import settings
from db.master_db import connect_master_db, close_master_db, get_master_db
from db.database_router import db_router, DatabaseRouter
from api.v1.api import api_router
from core.security import get_current_active_user
from models.user import AdminUserInDB

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_master_db()
    
    # Initialize the database router
    master_db = get_master_db()
    global db_router
    db_router = DatabaseRouter(master_db)
    
    yield
    
    # Shutdown
    await close_master_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Tenant Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add middleware for tenant identification
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Skip middleware for auth endpoints
    if request.url.path.startswith(f"{settings.API_V1_STR}/auth"):
        return await call_next(request)
    
    # Extract JWT token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            # Add tenant_id to request state
            if "tenant_id" in payload:
                request.state.tenant_id = payload["tenant_id"]
            
        except Exception as e:
            # If token is invalid, continue without setting tenant_id
            pass
    
    response = await call_next(request)
    return response

# Include API router
app.include_router(api_router, prefix="/org", tags=["Organization"])

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not Found"},
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Multi-Tenant Backend API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )
