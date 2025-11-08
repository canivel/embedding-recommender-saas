# Observability Integration Guide

This guide explains how to integrate observability (metrics, logging, tracing) into each service in the Embedding Recommender SaaS platform.

## Table of Contents
1. [Backend API Integration](#backend-api-integration)
2. [ML Engine Integration](#ml-engine-integration)
3. [Data Pipeline Integration](#data-pipeline-integration)
4. [Frontend Integration](#frontend-integration)
5. [Common Patterns](#common-patterns)

---

## Backend API Integration

### Prerequisites
```bash
pip install prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
pip install python-json-logger
```

### 1. Add Prometheus Metrics

**File: `backend-api/metrics.py`**

```python
from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint'],
)

# Business metrics
recommendations_served_total = Counter(
    'recommendations_served_total',
    'Total recommendations served',
    ['tenant_id', 'model_version'],
)

api_usage_tokens_total = Counter(
    'api_usage_tokens_total',
    'Total API tokens consumed',
    ['tenant_id', 'endpoint'],
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# Cache metrics
cache_hits_total = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
cache_misses_total = Counter('cache_misses_total', 'Cache misses', ['cache_type'])
```

### 2. Setup Structured Logging

**File: `backend-api/logging.py`**

```python
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

def setup_json_logging(service_name: str):
    """Configure JSON structured logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # JSON formatter with standard fields
    json_handler = logging.StreamHandler()
    json_formatter = jsonlogger.JsonFormatter()

    # Add custom fields to all logs
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            log_record['service'] = service_name
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            log_record['level'] = record.levelname

            # Add trace context from OpenTelemetry
            from opentelemetry import trace
            span = trace.get_current_span()
            if span and span.is_recording():
                ctx = span.get_span_context()
                log_record['trace_id'] = format(ctx.trace_id, '032x')
                log_record['span_id'] = format(ctx.span_id, '016x')

    json_handler.setFormatter(CustomJsonFormatter())
    logger.addHandler(json_handler)

    return logger

logger = setup_json_logging('backend-api')
```

### 3. Add OpenTelemetry Tracing

**File: `backend-api/tracing.py`**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import os

def init_tracing():
    """Initialize OpenTelemetry tracing"""

    # Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv('JAEGER_AGENT_HOST', 'localhost'),
        agent_port=int(os.getenv('JAEGER_AGENT_PORT', 6831)),
    )

    # Tracer provider
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(trace_provider)

    return trace.get_tracer(__name__)

tracer = init_tracing()

def instrument_app(app):
    """Auto-instrument FastAPI application"""
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
```

### 4. Add Middleware for Request Tracking

**File: `backend-api/middleware.py`**

```python
import time
import uuid
from fastapi import Request, Response
from opentelemetry import trace, context
from opentelemetry.trace import Status, StatusCode

from .metrics import (
    http_requests_total, http_request_duration_seconds,
    http_requests_in_progress
)
from .logging import logger

async def observability_middleware(request: Request, call_next):
    """Track request metrics, logging, and tracing"""

    # Generate or extract trace ID
    trace_id = request.headers.get('x-trace-id', str(uuid.uuid4()))
    span_id = request.headers.get('x-span-id', str(uuid.uuid4()))

    # Normalize path to avoid high cardinality
    path = request.url.path
    if request.url.query:
        path = f"{path}?query"

    endpoint = f"{request.method} {path}"

    # Track in-progress requests
    http_requests_in_progress.labels(
        method=request.method,
        endpoint=endpoint
    ).inc()

    start_time = time.time()
    status_code = 500

    # Start span
    with trace.get_tracer(__name__).start_as_current_span(endpoint) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("trace_id", trace_id)

        try:
            response = await call_next(request)
            status_code = response.status_code

        except Exception as exc:
            status_code = 500
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            raise

        finally:
            # Record metrics
            duration = time.time() - start_time

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
                status=status_code
            ).observe(duration)

            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=status_code
            ).inc()

            http_requests_in_progress.labels(
                method=request.method,
                endpoint=endpoint
            ).dec()

            # Set span attributes
            span.set_attribute("http.status_code", status_code)
            span.set_attribute("http.duration_ms", duration * 1000)

            # Log request
            logger.info(
                f"HTTP {request.method} {path}",
                extra={
                    "endpoint": endpoint,
                    "method": request.method,
                    "status_code": status_code,
                    "latency_ms": duration * 1000,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "path": path,
                }
            )

    # Add trace headers to response
    response.headers["x-trace-id"] = trace_id
    response.headers["x-span-id"] = span_id

    return response
```

### 5. Instrument Business Logic

**File: `backend-api/recommendations.py`**

```python
from opentelemetry import trace
from .metrics import recommendations_served_total, api_usage_tokens_total
from .logging import logger

tracer = trace.get_tracer(__name__)

async def get_recommendations(request: RecommendationRequest, tenant_id: str):
    """Get recommendations with full instrumentation"""

    with tracer.start_as_current_span("get_recommendations") as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("user_id", request.user_id)
        span.set_attribute("num_items", request.num_items)

        # Auth span
        with tracer.start_as_current_span("authenticate"):
            # ... auth logic ...
            pass

        # ML Engine call span
        with tracer.start_as_current_span("ml_engine_call"):
            logger.debug("Calling ML engine", extra={
                "tenant_id": tenant_id,
                "user_id": request.user_id
            })
            recommendations = await ml_client.get_recommendations(
                tenant_id=tenant_id,
                user_id=request.user_id,
                num_items=request.num_items
            )

        # Log usage span
        with tracer.start_as_current_span("log_usage"):
            await log_api_usage(
                tenant_id=tenant_id,
                endpoint="/api/v1/recommendations",
                tokens_used=request.num_items
            )

            # Record metrics
            recommendations_served_total.labels(
                tenant_id=tenant_id,
                model_version="v1.0"
            ).inc()

            api_usage_tokens_total.labels(
                tenant_id=tenant_id,
                endpoint="/api/v1/recommendations"
            ).inc(request.num_items)

        logger.info("Recommendations served", extra={
            "tenant_id": tenant_id,
            "count": len(recommendations),
            "status": "success"
        })

        return recommendations
```

### 6. Expose Metrics Endpoint

**File: `backend-api/main.py`**

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CollectorRegistry
from starlette.middleware import Middleware

from .middleware import observability_middleware
from .tracing import init_tracing, instrument_app
from .logging import setup_json_logging
from .metrics import registry  # Import your metrics registry

# Setup observability
setup_json_logging('backend-api')
init_tracing()

# Create app
app = FastAPI(title="Backend API")

# Add middleware
app.middleware("http")(observability_middleware)

# Instrument app
instrument_app(app)

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(registry))

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## ML Engine Integration

### 1. Training Job Metrics

**File: `ml-engine/training.py`**

```python
from prometheus_client import Counter, Histogram, Gauge
import time
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

# Metrics
training_job_total = Counter(
    'training_job_total',
    'Total training jobs',
    ['tenant_id', 'model_type']
)

training_job_duration_seconds = Histogram(
    'training_job_duration_seconds',
    'Training job duration',
    ['tenant_id', 'model_type'],
    buckets=(60, 300, 600, 1800, 3600, 7200)
)

training_job_failures_total = Counter(
    'training_job_failures_total',
    'Training job failures',
    ['tenant_id', 'error_type']
)

ml_recommendation_quality = Gauge(
    'ml_recommendation_quality',
    'Model quality metrics',
    ['tenant_id', 'metric']
)

class ModelTrainer:
    def train(self, tenant_id: str, model_type: str = "two-tower"):
        job_id = f"job_{int(time.time())}"
        training_job_total.labels(
            tenant_id=tenant_id,
            model_type=model_type
        ).inc()

        with tracer.start_as_current_span("train_model") as span:
            span.set_attribute("tenant_id", tenant_id)
            span.set_attribute("job_id", job_id)

            start = time.time()
            try:
                # Training logic here
                with tracer.start_as_current_span("data_loading"):
                    data = self._load_data(tenant_id)

                with tracer.start_as_current_span("feature_engineering"):
                    features = self._engineer_features(data)

                with tracer.start_as_current_span("model_training"):
                    model = self._train_model(features)

                with tracer.start_as_current_span("model_evaluation"):
                    metrics = self._evaluate(model)

                # Record metrics
                training_job_duration_seconds.labels(
                    tenant_id=tenant_id,
                    model_type=model_type
                ).observe(time.time() - start)

                ml_recommendation_quality.labels(
                    tenant_id=tenant_id,
                    metric="ndcg_10"
                ).set(metrics['ndcg_10'])

                return {"status": "success", "job_id": job_id}

            except Exception as e:
                training_job_failures_total.labels(
                    tenant_id=tenant_id,
                    error_type=type(e).__name__
                ).inc()
                raise
```

### 2. Inference Metrics

**File: `ml-engine/inference.py`**

```python
from prometheus_client import Histogram
import time

ml_model_inference_duration = Histogram(
    'ml_model_inference_duration_seconds',
    'Inference duration',
    ['operation', 'model_version'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5)
)

def get_recommendations(user_embedding, top_k=10):
    """Get recommendations with latency tracking"""
    with tracer.start_as_current_span("get_recommendations"):

        # Embedding lookup
        with tracer.start_as_current_span("embedding_lookup"):
            start = time.time()
            # ... lookup logic ...
            ml_model_inference_duration.labels(
                operation="embedding_lookup",
                model_version="v1.0"
            ).observe(time.time() - start)

        # ANN search
        with tracer.start_as_current_span("ann_search"):
            start = time.time()
            # ... ANN search ...
            ml_model_inference_duration.labels(
                operation="ann_search",
                model_version="v1.0"
            ).observe(time.time() - start)

        # Reranking
        with tracer.start_as_current_span("reranking"):
            start = time.time()
            # ... reranking ...
            ml_model_inference_duration.labels(
                operation="reranking",
                model_version="v1.0"
            ).observe(time.time() - start)

        return recommendations
```

---

## Data Pipeline Integration

### ETL Metrics

**File: `data-pipeline/etl.py`**

```python
from prometheus_client import Counter, Histogram, Gauge
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Metrics
data_ingestion_records_total = Counter(
    'data_ingestion_records_total',
    'Records ingested',
    ['tenant_id', 'data_type']
)

data_pipeline_duration_seconds = Histogram(
    'data_pipeline_duration_seconds',
    'Pipeline stage duration',
    ['tenant_id', 'stage'],
    buckets=(1, 10, 60, 300, 1800)
)

data_validation_errors_total = Counter(
    'data_validation_errors_total',
    'Validation errors',
    ['tenant_id', 'error_type']
)

def run_etl_pipeline(tenant_id: str):
    """Run ETL pipeline with observability"""

    with tracer.start_as_current_span("etl_pipeline") as span:
        span.set_attribute("tenant_id", tenant_id)

        # Extraction
        with tracer.start_as_current_span("extract"):
            import time
            start = time.time()
            data = extract_data(tenant_id)
            duration = time.time() - start

            data_pipeline_duration_seconds.labels(
                tenant_id=tenant_id,
                stage="extract"
            ).observe(duration)

            logger.info(f"Extracted {len(data)} records", extra={
                "tenant_id": tenant_id,
                "record_count": len(data),
                "duration_seconds": duration
            })

        # Transformation & Validation
        with tracer.start_as_current_span("transform"):
            start = time.time()

            errors = {}
            for record in data:
                if not validate_record(record):
                    error_type = get_error_type(record)
                    errors[error_type] = errors.get(error_type, 0) + 1

            # Record validation errors
            for error_type, count in errors.items():
                data_validation_errors_total.labels(
                    tenant_id=tenant_id,
                    error_type=error_type
                ).inc(count)

            transformed_data = transform_data(data)
            duration = time.time() - start

            data_pipeline_duration_seconds.labels(
                tenant_id=tenant_id,
                stage="transform"
            ).observe(duration)

        # Loading
        with tracer.start_as_current_span("load"):
            start = time.time()
            load_data(tenant_id, transformed_data)
            duration = time.time() - start

            data_ingestion_records_total.labels(
                tenant_id=tenant_id,
                data_type="user_interactions"
            ).inc(len(transformed_data))

            data_pipeline_duration_seconds.labels(
                tenant_id=tenant_id,
                stage="load"
            ).observe(duration)

            logger.info(f"Loaded {len(transformed_data)} records", extra={
                "tenant_id": tenant_id,
                "record_count": len(transformed_data),
                "duration_seconds": duration
            })
```

---

## Frontend Integration

### Browser Tracing and Monitoring

**File: `frontend/instrumentation.ts`**

```typescript
import { WebTracerProvider, BatchSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { JaegerExporter } from '@opentelemetry/exporter-trace-jaeger-web';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

// Initialize tracing
const jaegerExporter = new JaegerExporter({
  endpoint: 'http://localhost:14268/api/traces',
});

const resource = Resource.default().merge(
  new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'frontend',
    environment: process.env.REACT_APP_ENV,
  })
);

const webTracerProvider = new WebTracerProvider({ resource });
webTracerProvider.addSpanProcessor(new BatchSpanProcessor(jaegerExporter));

// Instrument fetch API
new FetchInstrumentation().instrumentationVersion;

// Export tracer
export const tracer = webTracerProvider.getTracer('frontend');
```

### Custom Metrics Reporting

```typescript
// Report Web Vitals to Prometheus
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendMetric(name: string, value: number, labels: Record<string, string>) {
  fetch('/metrics/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, value, labels })
  });
}

getCLS(metric => sendMetric('web_vital_cls', metric.value, {}));
getFID(metric => sendMetric('web_vital_fid', metric.value, {}));
getLCP(metric => sendMetric('web_vital_lcp', metric.value, {}));
```

---

## Common Patterns

### 1. Database Instrumentation

```python
@contextmanager
def track_db_query(query_type: str, table: str):
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        db_query_duration_seconds.labels(
            query_type=query_type,
            table=table
        ).observe(duration)
```

### 2. Cache Operations

```python
def cached_get(key: str, cache_type: str):
    if key in cache:
        cache_hits_total.labels(cache_type=cache_type).inc()
        return cache[key]
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()
        value = fetch_value(key)
        cache[key] = value
        return value
```

### 3. Error Tracking

```python
try:
    # ... operation ...
except Exception as e:
    error_counter.labels(error_type=type(e).__name__).inc()
    span.record_exception(e)
    logger.error(str(e), extra={"exception": type(e).__name__})
    raise
```

### 4. Distributed Tracing with Propagation

```python
# Incoming request
trace_id = request.headers.get('traceparent')
span.set_attribute('http.request_content_length', len(request.body))

# Outgoing request
headers['traceparent'] = span.get_span_context()
```

---

## Checklist for Each Service

- [ ] Add prometheus-client and opentelemetry libraries
- [ ] Define key metrics (system, application, business)
- [ ] Setup structured JSON logging
- [ ] Initialize OpenTelemetry tracing
- [ ] Add middleware/interceptors for automatic tracking
- [ ] Instrument business logic with spans
- [ ] Expose `/metrics` endpoint
- [ ] Add log statements with structured context
- [ ] Test metric collection (curl endpoint)
- [ ] Test log ingestion (check Loki)
- [ ] Test trace reporting (check Jaeger)
- [ ] Update prometheus.yml scrape_configs
- [ ] Document service-specific metrics

---

## Testing Instrumentation

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics | grep http_requests_total
```

### Logs
```bash
curl 'http://localhost:3100/loki/api/v1/query_range?query={service="backend-api"}'
```

### Traces
```bash
# Open Jaeger UI
open http://localhost:16686
```

## Support

For issues or questions about observability integration:
1. Check the example code in `/observability/examples/`
2. Review the README.md
3. Consult OpenTelemetry and Prometheus documentation
