from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import init_db, engine
from app.config import get_settings
from app.archive import get_archive_writer
from app.models import HealthResponse
from app.routes import events, export, verify


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and other resources on startup."""
    init_db()
    yield


app = FastAPI(
    title="AI Action Ledger",
    description="Tamper-evident, append-only logging system for AI actions",
    version="1.1.0",
    lifespan=lifespan
)

# CORS configuration
cors_origins = os.environ.get("CORS_ALLOW_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)
app.include_router(export.router)
app.include_router(verify.router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Action Ledger",
        "version": "1.1.0",
        "docs": "/docs",
        "endpoints": {
            "events": "/events",
            "export": "/export",
            "verify": "/verify",
            "health": "/health"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint. Verifies database and archive connectivity."""
    from sqlalchemy import text

    # Check database
    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check archive
    archive_status = "healthy"
    try:
        writer = get_archive_writer()
        if not writer.check_health():
            archive_status = "unhealthy: cannot write to archive"
    except Exception as e:
        archive_status = f"unhealthy: {str(e)}"

    overall_status = "healthy" if db_status == "healthy" and archive_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        archive=archive_status
    )