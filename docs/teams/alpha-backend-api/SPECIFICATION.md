# Team Alpha: Customer-Facing Backend API

## Mission
Build the primary REST API that customers interact with, handling authentication, rate limiting, multi-tenancy, and orchestrating calls to ML and data services.

## Technology Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic v2
- **Testing**: pytest, httpx
- **Documentation**: OpenAPI/Swagger (auto-generated)

## Architecture

### Directory Structure
```
backend-api/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── recommendations.py
│   │   │   ├── interactions.py
│   │   │   ├── items.py
│   │   │   ├── auth.py
│   │   │   └── usage.py
│   │   └── admin/
│   │       ├── tenants.py
│   │       └── api_keys.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── rate_limiter.py
│   │   └── middleware.py
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── repositories.py
│   ├── services/
│   │   ├── ml_client.py
│   │   ├── data_pipeline_client.py
│   │   └── usage_tracker.py
│   └── main.py
├── migrations/
│   └── alembic/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Database Schema

### Tables

#### tenants
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) UNIQUE NOT NULL,
    plan VARCHAR(32) NOT NULL CHECK (plan IN ('starter', 'pro', 'enterprise')),
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
```

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL CHECK (role IN ('admin', 'developer', 'viewer')),
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
```

#### api_keys
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(32) NOT NULL,
    permissions JSONB DEFAULT '["read", "write"]',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_tenant_id ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

#### usage_logs
```sql
CREATE TABLE usage_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INT NOT NULL,
    latency_ms INT NOT NULL,
    request_size_bytes INT,
    response_size_bytes INT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Partitioned by month for scalability
CREATE INDEX idx_usage_logs_tenant_timestamp ON usage_logs(tenant_id, timestamp DESC);
CREATE INDEX idx_usage_logs_timestamp ON usage_logs(timestamp DESC);
```

#### rate_limits
```sql
CREATE TABLE rate_limits (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    requests_per_minute INT NOT NULL DEFAULT 1000,
    requests_per_hour INT NOT NULL DEFAULT 50000,
    requests_per_day INT NOT NULL DEFAULT 1000000,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Core Components

### 1. Authentication & Authorization

**src/core/security.py**
```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"  # From environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_api_key(key: str) -> Optional[Tenant]:
    # Hash the key and lookup in database
    # Return tenant if valid, None otherwise
    pass
```

### 2. Rate Limiting

**src/core/rate_limiter.py**
```python
from fastapi import Request, HTTPException
from redis import Redis
import time

redis_client = Redis(host='redis', port=6379, decode_responses=True)

async def rate_limit_middleware(request: Request, call_next):
    tenant_id = request.state.tenant_id  # Set by auth middleware

    # Token bucket algorithm
    key = f"rate_limit:{tenant_id}:{int(time.time() / 60)}"  # Per minute

    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 60)  # Expire after 1 minute

    limit = await get_tenant_rate_limit(tenant_id)

    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current))

    return response
```

### 3. Multi-Tenancy

**src/core/middleware.py**
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from API key or JWT
        tenant_id = await extract_tenant_from_request(request)
        request.state.tenant_id = tenant_id

        # Set tenant-specific database schema or filter
        # (Row-level security in PostgreSQL)

        response = await call_next(request)
        return response
```

### 4. ML Engine Client

**src/services/ml_client.py**
```python
import httpx
from typing import List, Dict

class MLEngineClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_recommendations(
        self,
        tenant_id: str,
        user_id: str,
        count: int = 10,
        filters: Dict = None
    ) -> List[Dict]:
        response = await self.client.post(
            f"{self.base_url}/internal/ml/recommendations",
            json={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "count": count,
                "filters": filters or {}
            }
        )
        response.raise_for_status()
        return response.json()

    async def generate_embeddings(
        self,
        tenant_id: str,
        items: List[Dict]
    ) -> List[Dict]:
        response = await self.client.post(
            f"{self.base_url}/internal/ml/embeddings",
            json={"tenant_id": tenant_id, "items": items}
        )
        response.raise_for_status()
        return response.json()
```

## API Endpoints

### Public API (v1)

#### POST /api/v1/recommendations
Get personalized recommendations for a user.

**Implementation:**
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()

class RecommendationRequest(BaseModel):
    user_id: str
    count: int = 10
    filters: Dict = {}

@router.post("/recommendations")
async def get_recommendations(
    request: RecommendationRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    # Call ML Engine
    ml_client = MLEngineClient(settings.ML_ENGINE_URL)
    recommendations = await ml_client.get_recommendations(
        tenant_id=tenant_id,
        user_id=request.user_id,
        count=request.count,
        filters=request.filters
    )

    # Log usage
    await log_api_usage(tenant_id, endpoint="/recommendations", latency_ms=...)

    return recommendations
```

#### POST /api/v1/interactions
Track user interactions.

#### POST /api/v1/items
Upload item catalog.

#### GET /api/v1/usage
Get usage statistics.

### Admin API

#### POST /api/admin/tenants
Create new tenant.

#### GET /api/admin/tenants/{tenant_id}
Get tenant details.

#### POST /api/admin/api-keys
Create API key.

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_auth.py
def test_create_access_token():
    token = create_access_token({"sub": "user@example.com"})
    assert token is not None
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user@example.com"

# tests/unit/test_rate_limiter.py
@pytest.mark.asyncio
async def test_rate_limit_enforced():
    # Mock Redis
    # Send 1001 requests
    # Assert 429 on 1001st request
    pass
```

### Integration Tests
```python
# tests/integration/test_recommendations_api.py
@pytest.mark.asyncio
async def test_get_recommendations_success(client, auth_headers):
    response = await client.post(
        "/api/v1/recommendations",
        json={"user_id": "user_123", "count": 5},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) <= 5
```

### Contract Tests
Use Pact to verify ML Engine and Data Pipeline contracts.

## Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      containers:
      - name: backend-api
        image: backend-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Monitoring & Observability

### Metrics (Prometheus)
```python
from prometheus_client import Counter, Histogram

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status_code']
)

api_latency = Histogram(
    'api_latency_seconds',
    'API request latency',
    ['endpoint']
)
```

### Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "request_processed",
    tenant_id=tenant_id,
    endpoint="/recommendations",
    duration_ms=45,
    status_code=200
)
```

## Security Checklist

- [ ] All passwords hashed with bcrypt
- [ ] JWT tokens with short expiration (15 min)
- [ ] API keys hashed in database
- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS properly configured
- [ ] Rate limiting per tenant
- [ ] Input validation on all endpoints
- [ ] HTTPS enforced (TLS 1.3)
- [ ] Secrets in environment variables (not code)
- [ ] Audit logging for admin actions

## Development Workflow

### Phase 1 (Weeks 1-2): Foundation
- [ ] Setup FastAPI project structure
- [ ] Database schema & migrations
- [ ] Authentication (JWT + API keys)
- [ ] Basic CRUD for tenants
- [ ] Health & readiness endpoints

### Phase 2 (Weeks 3-4): Core API
- [ ] Recommendations endpoint (mock ML client)
- [ ] Interactions endpoint
- [ ] Items upload endpoint
- [ ] Usage tracking
- [ ] Rate limiting

### Phase 3 (Weeks 5-6): Integration
- [ ] Integrate with real ML Engine
- [ ] Integrate with Data Pipeline
- [ ] Admin API endpoints
- [ ] API key management

### Phase 4 (Weeks 7-8): Polish
- [ ] Comprehensive tests (80%+ coverage)
- [ ] OpenAPI documentation
- [ ] Performance optimization
- [ ] Production deployment

## Success Criteria

- API latency p95 < 100ms
- 100% uptime (with health checks)
- Zero SQL injection vulnerabilities
- Rate limiting working correctly
- All endpoints documented (OpenAPI)
- Test coverage > 80%
