"""Data Pipeline FastAPI Application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .api import upload_router, health_router, validation_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.version}")

    # Initialize connections
    try:
        from .storage.s3_client import s3_client
        logger.info("S3 client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")

    try:
        from .kafka.producer import kafka_producer
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.service_name}")

    try:
        from .kafka.producer import kafka_producer
        kafka_producer.close()
        logger.info("Kafka producer closed")
    except Exception as e:
        logger.error(f"Error closing Kafka producer: {e}")


# Create FastAPI app
app = FastAPI(
    title="Data Pipeline Service",
    description="Data ingestion, validation, and ETL pipeline for Embedding Recommender SaaS",
    version=settings.version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(validation_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "upload_csv": "/internal/data/upload-csv",
            "upload_interactions": "/internal/data/interactions",
            "upload_items": "/internal/data/items",
            "validate": "/api/validation/validate",
            "schema": "/api/validation/schema/{data_type}",
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level=settings.log_level.lower()
    )
