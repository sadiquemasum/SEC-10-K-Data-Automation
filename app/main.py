from fastapi import FastAPI, HTTPException

from app.database import check_database_connection

from contextlib import asynccontextmanager

from app.database import Base, engine
from app.models.company import Company
from app.routers.companies import router as companies_router
from app.models.filing import Filing
from app.routers.filings import router as filings_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    yield

app = FastAPI(
    title="FastAPI Docker Application",
    description="SEC 10-K Data Automation",
    version="1.0.0",
    lifespan=lifespan
)

# Register routers
app.include_router(companies_router)
app.include_router(filings_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to SEC 10-K Downloader FastAPI!",
        "python": "3.14.3",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/db-health")
async def database_health_check():

    if check_database_connection():
        return {
            "database": "PostgreSQL",
            "status": "connected"
        }

    raise HTTPException(
        status_code=503,
        detail="Database connection failed"
    )