"""
Backend API Instrumentation Example
This example shows how to instrument a FastAPI backend service with:
- Prometheus metrics (HTTP requests, latency, errors)
- Structured logging (JSON format with trace IDs)
- Distributed tracing (Jaeger via OpenTelemetry)
"""

import json
import time
import logging
from datetime import datetime
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry
from prometheus_client.core import ContentTypeMiddleware
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from pythonjsonlogger import jsonlogger


# ============================================================================
# PROMETHEUS METRICS SETUP
# ============================================================================

registry = CollectorRegistry()

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# Application-level metrics
recommendations_served_total = Counter(
    'recommendations_served_total',
    'Total recommendations served',
    ['tenant_id', 'model_version'],
    registry=registry
)

recommendation_quality = Gauge(
    'recommendation_quality',
    'Recommendation quality metrics',
    ['tenant_id', 'metric'],
    registry=registry
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

cache_operations_duration_seconds = Histogram(
    'cache_operations_duration_seconds',
    'Cache operation duration',
    ['cache_type', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1),
    registry=registry
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['pool_name'],
    registry=registry
)


# ============================================================================
# STRUCTURED LOGGING SETUP
# ============================================================================

class StructuredJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['service'] = 'backend-api'

        # Add trace context if available
        span = trace.get_current_span()
        if span and span.is_recording():
            log_record['trace_id'] = format(span.get_span_context().trace_id, '032x')
            log_record['span_id'] = format(span.get_span_context().span_id, '016x')


def setup_logging():
    """Configure structured JSON logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # JSON handler
    json_handler = logging.StreamHandler()
    json_formatter = StructuredJSONFormatter('%(message)s')
    json_handler.setFormatter(json_formatter)
    logger.addHandler(json_handler)

    return logger


# ============================================================================
# JAEGER TRACING SETUP
# ============================================================================

def setup_tracing():
    """Configure Jaeger distributed tracing"""
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )

    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(trace_provider)

    return trace.get_tracer(__name__)


# ============================================================================
# FASTAPI APPLICATION WITH INSTRUMENTATION
# ============================================================================

# Initialize logging and tracing
logger = setup_logging()
tracer = setup_tracing()

# Create FastAPI app
app = FastAPI(title="Backend API", version="1.0.0")

# Add Prometheus metrics endpoint
from fastapi.responses import PlainTextResponse

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(registry))


# ============================================================================
# MIDDLEWARE FOR REQUEST TRACKING
# ============================================================================

@app.middleware("http")
async def tracking_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to track:
    - Request duration and latency
    - Error rates
    - In-progress requests
    - Trace context propagation
    """

    # Extract or create trace context
    trace_id = request.headers.get('x-trace-id', str(uuid4()))
    span_id = request.headers.get('x-span-id', str(uuid4()))

    # Extract path and clean it for metrics (avoid high cardinality)
    path = request.url.path
    # Normalize paths: /api/v1/users/123 -> /api/v1/users/{id}
    if '/api/' in path:
        parts = path.split('/')
        for i, part in enumerate(parts):
            if part.isdigit() or (part.startswith('{') and part.endswith('}')):
                parts[i] = '{id}'
        path = '/'.join(parts)

    method = request.method
    endpoint = f"{method} {path}"

    # Track in-progress requests
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    # Start trace
    with tracer.start_as_current_span(f"{method} {path}") as span:
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.target", path)
        span.set_attribute("trace_id", trace_id)
        span.set_attribute("span_id", span_id)

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            logger.error(
                f"Request failed: {endpoint}",
                extra={
                    "endpoint": endpoint,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "error": str(exc),
                    "exception": type(exc).__name__
                }
            )
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).observe(duration)
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

            # Set span attributes
            span.set_attribute("http.status_code", status_code)
            span.set_attribute("http.duration_ms", duration * 1000)

            # Log structured request info
            logger.info(
                f"HTTP {method} {path}",
                extra={
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "latency_ms": duration * 1000,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "timestamp": datetime.utcnow().isoformat() + 'Z'
                }
            )

    # Add trace headers to response
    response.headers["x-trace-id"] = trace_id
    response.headers["x-span-id"] = span_id

    return response


# ============================================================================
# EXAMPLE ENDPOINTS WITH BUSINESS LOGIC TRACING
# ============================================================================

@app.post("/api/v1/recommendations")
async def get_recommendations(request: Request):
    """
    Get recommendations for a user.
    Demonstrates:
    - Business logic tracing
    - Nested spans
    - Metrics recording
    - Structured logging
    """
    with tracer.start_as_current_span("get_recommendations") as span:
        body = await request.json()
        tenant_id = body.get("tenant_id")
        user_id = body.get("user_id")

        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("user_id", user_id)

        logger.info(
            "Getting recommendations",
            extra={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        )

        # Simulate authentication
        with tracer.start_as_current_span("authenticate"):
            auth_start = time.time()
            # ... auth logic ...
            auth_duration = time.time() - auth_start
            logger.debug("Authentication successful", extra={"duration_ms": auth_duration * 1000})

        # Simulate cache lookup
        cache_hit = False
        with tracer.start_as_current_span("embedding_cache_lookup"):
            cache_start = time.time()
            # ... cache logic ...
            cache_hit = True  # simulated
            cache_duration = time.time() - cache_start

            if cache_hit:
                cache_hits_total.labels(cache_type="embeddings").inc()
            else:
                cache_misses_total.labels(cache_type="embeddings").inc()

            cache_operations_duration_seconds.labels(
                cache_type="embeddings",
                operation="get"
            ).observe(cache_duration)

        # Simulate ML Engine call
        with tracer.start_as_current_span("ml_engine_call"):
            ml_start = time.time()
            # ... ML engine logic ...
            ml_duration = time.time() - ml_start
            recommendations = [
                {"item_id": "item_1", "score": 0.95},
                {"item_id": "item_2", "score": 0.87},
            ]
            logger.debug("ML Engine returned recommendations", extra={
                "count": len(recommendations),
                "duration_ms": ml_duration * 1000
            })

        # Record business metrics
        recommendations_served_total.labels(
            tenant_id=tenant_id,
            model_version="v1.0"
        ).inc()

        recommendation_quality.labels(
            tenant_id=tenant_id,
            metric="ndcg_10"
        ).set(0.42)

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "backend-api",
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }


# ============================================================================
# AUTO-INSTRUMENTATION
# ============================================================================

# Auto-instrument FastAPI and HTTP clients
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
RequestsInstrumentor().instrument()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
