# API Contracts & Interface Definitions

This document defines the contracts between all system components to enable parallel development.

## 1. Backend API (Team Alpha) → ML Engine (Team Beta)

### Get Recommendations

**Endpoint:** `POST /internal/ml/recommendations`

**Request:**
```json
{
  "tenant_id": "uuid",
  "user_id": "string",
  "context": {
    "device_type": "mobile|desktop|tablet",
    "location": "string",
    "session_id": "string"
  },
  "filters": {
    "categories": ["string"],
    "min_score": 0.5,
    "exclude_ids": ["string"]
  },
  "count": 10,
  "model_version": "string (optional)"
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "recommendations": [
    {
      "item_id": "string",
      "score": 0.95,
      "embedding_distance": 0.23,
      "metadata": {
        "category": "string",
        "created_at": "iso8601"
      }
    }
  ],
  "model_version": "v1.2.3",
  "latency_ms": 45,
  "cache_hit": true
}
```

### Generate Embeddings

**Endpoint:** `POST /internal/ml/embeddings`

**Request:**
```json
{
  "tenant_id": "uuid",
  "items": [
    {
      "item_id": "string",
      "features": {
        "title": "string",
        "description": "string",
        "category": "string",
        "tags": ["string"],
        "image_url": "string (optional)"
      }
    }
  ],
  "model_version": "string (optional)"
}
```

**Response:**
```json
{
  "embeddings": [
    {
      "item_id": "string",
      "embedding": [0.123, -0.456, ...],
      "dimension": 128
    }
  ],
  "model_version": "v1.2.3"
}
```

### Trigger Model Training

**Endpoint:** `POST /internal/ml/training/trigger`

**Request:**
```json
{
  "tenant_id": "uuid",
  "training_config": {
    "model_type": "matrix_factorization|two_tower|gnn",
    "hyperparameters": {
      "embedding_dim": 128,
      "learning_rate": 0.001,
      "epochs": 10
    },
    "data_range": {
      "start_date": "iso8601",
      "end_date": "iso8601"
    }
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "queued|running|completed|failed",
  "estimated_duration_minutes": 120
}
```

---

## 2. Backend API (Team Alpha) → Data Pipeline (Team Eta)

### Upload Interaction Data

**Endpoint:** `POST /internal/data/interactions`

**Request:**
```json
{
  "tenant_id": "uuid",
  "interactions": [
    {
      "user_id": "string",
      "item_id": "string",
      "interaction_type": "view|click|purchase|like|dislike",
      "timestamp": "iso8601",
      "context": {
        "device_type": "string",
        "session_id": "string"
      },
      "metadata": {}
    }
  ]
}
```

**Response:**
```json
{
  "accepted": 1500,
  "rejected": 0,
  "validation_errors": []
}
```

### Upload Item Catalog

**Endpoint:** `POST /internal/data/items`

**Request:**
```json
{
  "tenant_id": "uuid",
  "items": [
    {
      "item_id": "string",
      "title": "string",
      "description": "string",
      "category": "string",
      "tags": ["string"],
      "metadata": {},
      "created_at": "iso8601"
    }
  ]
}
```

**Response:**
```json
{
  "accepted": 1000,
  "rejected": 5,
  "validation_errors": [
    {
      "item_id": "item_123",
      "error": "Missing required field: title"
    }
  ]
}
```

---

## 3. Data Pipeline (Team Eta) → ML Engine (Team Beta)

### Training Data Format (S3)

**Location:** `s3://bucket/tenants/{tenant_id}/training_data/{date}/`

**File Format:** Parquet

**Schema:**
```python
{
  "user_id": str,
  "item_id": str,
  "interaction_type": str,
  "timestamp": int64,  # Unix timestamp
  "label": float,  # 0.0 (negative) to 1.0 (positive)
  "features": {
    "user_features": {...},
    "item_features": {...},
    "context_features": {...}
  }
}
```

**Partitioning:** By `date` and `tenant_id`

**Catalog File:** `s3://bucket/tenants/{tenant_id}/catalog.json`
```json
{
  "tenant_id": "uuid",
  "data_version": "v1.2.3",
  "partitions": [
    {
      "date": "2025-01-01",
      "path": "s3://...",
      "row_count": 1000000,
      "file_size_mb": 250
    }
  ],
  "schema_version": "1.0",
  "updated_at": "iso8601"
}
```

---

## 4. Control Plane (Team Epsilon) → All Services

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "version": "1.2.3",
  "uptime_seconds": 86400,
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "dependencies": "healthy"
  }
}
```

### Readiness Check

**Endpoint:** `GET /ready`

**Response:**
```json
{
  "ready": true
}
```

### Metrics Endpoint

**Endpoint:** `GET /metrics`

**Format:** Prometheus exposition format

**Example:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/recommendations",status="200"} 12453

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.05"} 10234
http_request_duration_seconds_bucket{le="0.1"} 12000
...
```

---

## 5. Backend API (Team Alpha) - Public REST API

### Authentication

**All endpoints require authentication via:**
- **API Key:** `Authorization: Bearer <api_key>` (for server-to-server)
- **JWT Token:** `Authorization: Bearer <jwt_token>` (for user sessions)

### Get Recommendations (Public)

**Endpoint:** `POST /api/v1/recommendations`

**Request:**
```json
{
  "user_id": "string",
  "count": 10,
  "filters": {
    "categories": ["electronics", "books"],
    "min_score": 0.5
  },
  "context": {
    "device_type": "mobile"
  }
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "item_id": "item_123",
      "score": 0.95
    }
  ],
  "metadata": {
    "model_version": "v1.2.3",
    "latency_ms": 45
  }
}
```

**Rate Limit:** 1000 requests/minute per tenant

### Track Interaction (Public)

**Endpoint:** `POST /api/v1/interactions`

**Request:**
```json
{
  "user_id": "string",
  "item_id": "string",
  "interaction_type": "view|click|purchase",
  "timestamp": "iso8601 (optional)"
}
```

**Response:**
```json
{
  "status": "accepted",
  "interaction_id": "uuid"
}
```

### Upload Items (Public)

**Endpoint:** `POST /api/v1/items`

**Request:**
```json
{
  "items": [
    {
      "item_id": "item_456",
      "title": "Product Name",
      "description": "Product description",
      "category": "electronics",
      "tags": ["smartphone", "5g"]
    }
  ]
}
```

**Response:**
```json
{
  "accepted": 1,
  "rejected": 0
}
```

### Get Item Embedding (Public)

**Endpoint:** `GET /api/v1/items/{item_id}/embedding`

**Response:**
```json
{
  "item_id": "item_123",
  "embedding": [0.123, -0.456, ...],
  "dimension": 128,
  "model_version": "v1.2.3"
}
```

### Get Usage Statistics (Public)

**Endpoint:** `GET /api/v1/usage`

**Query Params:** `?start_date=2025-01-01&end_date=2025-01-31`

**Response:**
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "metrics": {
    "api_calls": 1500000,
    "recommendations_served": 1200000,
    "items_indexed": 50000,
    "average_latency_ms": 45
  },
  "quota": {
    "api_calls_limit": 2000000,
    "api_calls_used": 1500000,
    "percentage_used": 75
  }
}
```

---

## 6. Frontend (Team Gamma) → Backend API (Team Alpha)

### Authentication Flow

**1. Login**

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "hashed_password"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "refresh_token": "jwt_refresh_token",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "tenant_id": "uuid",
    "role": "admin|developer|viewer"
  }
}
```

**2. Refresh Token**

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_token",
  "expires_in": 900
}
```

### Tenant Management

**Get Tenant Info**

**Endpoint:** `GET /api/v1/tenant`

**Response:**
```json
{
  "tenant_id": "uuid",
  "name": "Acme Corp",
  "plan": "starter|pro|enterprise",
  "status": "active|suspended",
  "created_at": "iso8601",
  "settings": {
    "default_model": "two_tower",
    "embedding_dimension": 128
  }
}
```

### API Key Management

**List API Keys**

**Endpoint:** `GET /api/v1/api-keys`

**Response:**
```json
{
  "keys": [
    {
      "id": "uuid",
      "name": "Production Key",
      "key_prefix": "sk_live_abc123",
      "created_at": "iso8601",
      "last_used_at": "iso8601",
      "status": "active|revoked"
    }
  ]
}
```

**Create API Key**

**Endpoint:** `POST /api/v1/api-keys`

**Request:**
```json
{
  "name": "Staging Key",
  "permissions": ["read", "write"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Staging Key",
  "key": "sk_test_xyz789_full_key_shown_once",
  "created_at": "iso8601"
}
```

---

## 7. Observability (Team Zeta) - Metrics Collection

### Standard Metrics (All Services)

**Labels:**
- `service`: Service name
- `endpoint`: API endpoint
- `method`: HTTP method
- `status_code`: HTTP status code
- `tenant_id`: Tenant identifier

**Metrics:**
```
# Request rate
http_requests_total{service, endpoint, method, status_code}

# Latency (histogram)
http_request_duration_seconds{service, endpoint, method}

# Error rate
http_errors_total{service, endpoint, error_type}

# Active connections
http_connections_active{service}

# Database queries
db_queries_total{service, query_type, table}
db_query_duration_seconds{service, query_type, table}

# Cache operations
cache_operations_total{service, operation, result}
cache_hit_rate{service}
```

### ML-Specific Metrics

```
# Model performance
ml_recommendation_quality{tenant_id, model_version, metric_name}

# Training metrics
ml_training_duration_seconds{tenant_id, model_type}
ml_training_loss{tenant_id, model_version, epoch}

# Serving metrics
ml_embedding_cache_hit_rate{tenant_id}
ml_ann_search_duration_seconds{tenant_id, index_size}
ml_recommendations_per_request{tenant_id}
```

### Logging Format

**Structured JSON logs:**
```json
{
  "timestamp": "2025-01-07T10:30:45Z",
  "level": "INFO|WARN|ERROR",
  "service": "backend-api",
  "trace_id": "uuid",
  "span_id": "uuid",
  "message": "Request processed",
  "context": {
    "tenant_id": "uuid",
    "user_id": "string",
    "endpoint": "/api/v1/recommendations",
    "duration_ms": 45,
    "status_code": 200
  }
}
```

---

## 8. Error Handling Standards

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {
      "field": "user_id",
      "reason": "Required field missing"
    },
    "request_id": "uuid",
    "timestamp": "iso8601"
  }
}
```

### Standard Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid request parameters |
| 401 | AUTHENTICATION_FAILED | Invalid or missing credentials |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |
| 503 | SERVICE_UNAVAILABLE | Service temporarily unavailable |

---

## 9. Data Validation Rules

### User ID
- Format: Alphanumeric, hyphens, underscores
- Max length: 128 characters
- Required: Yes

### Item ID
- Format: Alphanumeric, hyphens, underscores
- Max length: 128 characters
- Required: Yes

### Interaction Type
- Allowed values: `view`, `click`, `purchase`, `like`, `dislike`, `add_to_cart`, `remove_from_cart`
- Required: Yes

### Timestamp
- Format: ISO 8601
- Timezone: UTC
- Required: No (defaults to current time)

### Category
- Format: Lowercase alphanumeric, hyphens
- Max length: 64 characters
- Required: No

### Tags
- Format: Array of strings
- Max items: 20
- Max length per tag: 32 characters
- Required: No

---

## 10. Service Discovery

### Internal Service URLs (Kubernetes)

```
backend-api.default.svc.cluster.local:8000
ml-engine.default.svc.cluster.local:8001
data-pipeline.default.svc.cluster.local:8002
```

### Environment Variables (All Services)

```bash
# Service identification
SERVICE_NAME=backend-api
SERVICE_VERSION=1.2.3

# Upstream dependencies
ML_ENGINE_URL=http://ml-engine:8001
DATA_PIPELINE_URL=http://data-pipeline:8002

# Databases
POSTGRES_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379

# Storage
S3_BUCKET=embeddings-saas-data
S3_REGION=us-west-2

# Observability
PROMETHEUS_PORT=9090
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
LOG_LEVEL=INFO
```

---

## Contract Testing

Each team must implement contract tests to verify their service adheres to these interfaces:

1. **Request/Response validation**: Ensure all fields match schema
2. **Error handling**: Return proper error codes and formats
3. **Rate limiting**: Respect rate limit headers
4. **Timeouts**: Fail gracefully after timeout
5. **Retries**: Implement exponential backoff

**Testing Tools:**
- Pact (consumer-driven contract testing)
- OpenAPI validators
- Postman/Newman for integration tests
