"""
Main FastAPI application for the Backend API.

This module initializes the FastAPI app and configures all routes, middleware, and dependencies.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import text
import structlog

from src.api.v1 import auth, recommendations, interactions, items, usage, api_keys
from src.api.admin import tenants
from src.core.config import settings
from src.core.middleware import (
    RequestLoggingMiddleware,
    TenantMiddleware,
    RateLimitMiddleware,
)
from src.core.rate_limiter import rate_limiter
from src.db.session import engine
from src.services.ml_client import ml_client
from src.services.data_pipeline_client import data_pipeline_client

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Application startup time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Initialize Redis for rate limiting
    await rate_limiter.initialize()
    logger.info("rate_limiter_initialized")

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Close connections
    await rate_limiter.close()
    await ml_client.close()
    await data_pipeline_client.close()
    await engine.dispose()

    logger.info("application_shutdown_complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Embedding Recommender SaaS Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add custom middleware (order matters!)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantMiddleware)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "timestamp": time.time(),
            }
        },
    )


# Health and metrics endpoints
@app.get("/health", tags=["health"])
async def health_check() -> Dict:
    """
    Health check endpoint.

    Returns the health status of the service and its dependencies.
    """
    checks = {}

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["database"] = "unhealthy"

    # Check Redis
    try:
        if rate_limiter.redis_client:
            await rate_limiter.redis_client.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "not_initialized"
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        checks["redis"] = "unhealthy"

    # Check ML Engine
    try:
        ml_healthy = await ml_client.health_check()
        checks["ml_engine"] = "healthy" if ml_healthy else "unhealthy"
    except Exception as e:
        logger.error("ml_engine_health_check_failed", error=str(e))
        checks["ml_engine"] = "unhealthy"

    # Check Data Pipeline
    try:
        dp_healthy = await data_pipeline_client.health_check()
        checks["data_pipeline"] = "healthy" if dp_healthy else "unhealthy"
    except Exception as e:
        logger.error("data_pipeline_health_check_failed", error=str(e))
        checks["data_pipeline"] = "unhealthy"

    # Determine overall status
    all_healthy = all(v == "healthy" for v in checks.values())
    status_str = "healthy" if all_healthy else "degraded"

    return {
        "status": status_str,
        "version": settings.APP_VERSION,
        "uptime_seconds": int(time.time() - app_start_time),
        "checks": checks,
    }


@app.get("/ready", tags=["health"])
async def readiness_check() -> Dict:
    """
    Readiness check endpoint.

    Returns whether the service is ready to accept traffic.
    """
    # Check if database is accessible
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}


@app.get("/metrics", tags=["metrics"])
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    return PlainTextResponse(generate_latest())


# Include API routers
# Public API v1
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
app.include_router(interactions.router, prefix="/api/v1", tags=["interactions"])
app.include_router(items.router, prefix="/api/v1", tags=["items"])
app.include_router(usage.router, prefix="/api/v1", tags=["usage"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["api-keys"])

# Admin API
app.include_router(tenants.router, prefix="/api/admin", tags=["admin"])


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


# Middleware to track request metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track request metrics for Prometheus."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
