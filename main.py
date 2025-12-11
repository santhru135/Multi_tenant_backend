import uvicorn
from fastapi import FastAPI
from db.master_db import connect_master_db, close_master_db, get_master_db
from routes import org_routes, admin_routes

app = FastAPI(title="Multi-Tenant Backend")

# Include Routers
app.include_router(org_routes.router)
app.include_router(admin_routes.router)

# Startup/Shutdown
@app.on_event("startup")
async def startup_db():
    await connect_master_db()

@app.on_event("shutdown")
async def shutdown_db():
    await close_master_db()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
