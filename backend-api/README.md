# Backend API

The primary REST API for the Embedding Recommender SaaS platform. This service handles authentication, rate limiting, multi-tenancy, and orchestrates calls to ML and data services.

## Features

- **Authentication**: JWT-based user authentication and API key support
- **Multi-tenancy**: Complete tenant isolation with per-tenant rate limiting
- **Rate Limiting**: Redis-based token bucket algorithm
- **API Management**: Full CRUD for API keys with secure hashing
- **Usage Tracking**: Comprehensive logging for billing and analytics
- **Health Monitoring**: Health checks and Prometheus metrics
- **Mock Services**: Mock ML Engine and Data Pipeline clients for development

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Cache**: Redis for rate limiting
- **Package Manager**: UV
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Metrics**: Prometheus
- **Logging**: Structlog (JSON)

## Getting Started

### Prerequisites

- Python 3.11+
- UV package manager
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies**:
```bash
cd backend-api
uv sync
```

3. **Set up environment variables**:
```bash
cp ../.env.example .env
# Edit .env with your configuration
```

4. **Run database migrations**:
```bash
uv run alembic upgrade head
```

5. **Seed the database** (optional):
```bash
uv run python scripts/seed_data.py
```

### Running the Service

#### Development Mode
```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Using Docker
```bash
docker-compose up backend-api
```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Authentication

The API supports two authentication methods:

#### 1. JWT Tokens (for user sessions)
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'

# Use token
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "count": 10}'
```

#### 2. API Keys (for server-to-server)
```bash
# Create API key (requires JWT)
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "permissions": ["read", "write"]
  }'

# Use API key
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "count": 10}'
```

### Key Endpoints

#### Public API (v1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/recommendations` | POST | Get recommendations |
| `/api/v1/interactions` | POST | Track user interaction |
| `/api/v1/items` | POST | Upload item catalog |
| `/api/v1/usage` | GET | Get usage statistics |
| `/api/v1/api-keys` | GET | List API keys |
| `/api/v1/api-keys` | POST | Create API key |

#### Admin API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/tenants` | GET | List all tenants |
| `/api/admin/tenants` | POST | Create new tenant |
| `/api/admin/tenants/{id}` | GET | Get tenant details |
| `/api/admin/tenants/{id}` | PUT | Update tenant |
| `/api/admin/tenants/{id}` | DELETE | Delete tenant |

#### Health & Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/metrics` | GET | Prometheus metrics |

## Rate Limiting

Rate limits are enforced per tenant:

- **Default Limits**:
  - 1,000 requests/minute
  - 50,000 requests/hour
  - 1,000,000 requests/day

**Response Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
```

**Rate Limit Exceeded** (429):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests"
  }
}
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {
      "field": "user_id",
      "reason": "Required field missing"
    },
    "request_id": "uuid",
    "timestamp": "2025-01-07T10:30:45Z"
  }
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Database Schema

### Tables

- **tenants**: Customer organizations
- **users**: Tenant administrators and developers
- **api_keys**: API keys for programmatic access
- **usage_logs**: API usage tracking
- **rate_limits**: Per-tenant rate limit configurations

### Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Show current revision
uv run alembic current
```

## Testing

### Run All Tests
```bash
uv run pytest
```

### Run Specific Test File
```bash
uv run pytest tests/unit/test_security.py
```

### Run with Coverage
```bash
uv run pytest --cov=src --cov-report=html
```

### Integration Tests
```bash
# Start dependencies
docker-compose up -d postgres redis

# Run integration tests
uv run pytest tests/integration
```

## Development

### Code Quality

```bash
# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Lint
uv run flake8 src tests

# Type checking
uv run mypy src
```

### Project Structure

```
backend-api/
├── src/
│   ├── api/
│   │   ├── v1/          # Public API endpoints
│   │   └── admin/       # Admin endpoints
│   ├── core/            # Core utilities
│   ├── db/              # Database models and repositories
│   ├── services/        # External service clients
│   ├── schemas/         # Pydantic schemas
│   └── main.py          # FastAPI app
├── migrations/          # Alembic migrations
├── tests/              # Tests
├── Dockerfile          # Container image
├── pyproject.toml      # UV project config
└── README.md
```

## Configuration

All configuration is managed via environment variables (see `.env.example`):

### Required Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/embeddings_saas
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

### Optional Variables

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT_PER_MINUTE=1000

# Upstream Services
ML_ENGINE_URL=http://ml-engine:8001
DATA_PIPELINE_URL=http://data-pipeline:8002

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Monitoring

### Prometheus Metrics

The service exposes Prometheus metrics at `/metrics`:

```
# Request metrics
http_requests_total{method="POST",endpoint="/api/v1/recommendations",status_code="200"}
http_request_duration_seconds{method="POST",endpoint="/api/v1/recommendations"}

# Database metrics
db_queries_total{query_type="select",table="tenants"}
db_query_duration_seconds{query_type="select",table="tenants"}

# Cache metrics
cache_operations_total{operation="get",result="hit"}
cache_hit_rate
```

### Structured Logging

All logs are output in JSON format:

```json
{
  "timestamp": "2025-01-07T10:30:45Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "uuid",
  "message": "Request processed",
  "context": {
    "tenant_id": "uuid",
    "endpoint": "/api/v1/recommendations",
    "duration_ms": 45,
    "status_code": 200
  }
}
```

## Troubleshooting

### Common Issues

**Database connection errors**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
psql postgresql://user:pass@localhost:5432/dbname
```

**Redis connection errors**:
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli ping
```

**Migration errors**:
```bash
# Reset database (WARNING: destroys data)
uv run alembic downgrade base
uv run alembic upgrade head
```

## Production Deployment

### Docker

```bash
docker build -t backend-api:latest .
docker run -p 8000:8000 --env-file .env backend-api:latest
```

### Kubernetes

See `infrastructure/kubernetes/backend-api/` for deployment manifests.

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests and linters
4. Submit pull request

## License

Proprietary - Internal use only

## Support

For questions or issues, contact the platform team.
