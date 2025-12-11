from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from db.master_db import get_master_db, close_connection
from routes import org_routes, admin_routes

app = FastAPI(title="Multi-Tenant Backend API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(org_routes.router)
app.include_router(admin_routes.router)

@app.on_event("startup")
async def startup_db_client():
    # Initialize the database connection
    get_master_db()  # This will initialize the connection
    print("✅ Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_connection()
    print("✅ Closed MongoDB connection")

@app.get("/", tags=["root"])
async def root():
    """Root endpoint for health checks."""
    return {"status": "ok", "message": "Multi-Tenant Backend Service is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)