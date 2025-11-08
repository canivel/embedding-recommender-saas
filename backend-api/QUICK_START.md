# Backend API - Quick Start Guide

Get the Backend API up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Or: Python 3.11+, PostgreSQL, Redis, UV

## Option 1: Docker (Recommended)

### 1. Start All Services
```bash
# From project root
docker-compose up -d backend-api
```

This will start:
- PostgreSQL database
- Redis cache
- Backend API service

### 2. Check Health
```bash
curl http://localhost:8000/health
```

### 3. Seed Database
```bash
docker-compose exec backend-api uv run python scripts/seed_data.py
```

### 4. Test API
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo-corp.com", "password": "password123"}'

# Save the access_token from response

# Get recommendations
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "count": 10}'
```

## Option 2: Local Development

### 1. Install Dependencies
```bash
cd backend-api

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Setup Database
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Create database
createdb embeddings_saas

# Run migrations
uv run alembic upgrade head

# Seed data
uv run python scripts/seed_data.py
```

### 3. Start API
```bash
# Development mode (with auto-reload)
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Visit API Docs
Open http://localhost:8000/docs

## Testing Authentication

### JWT Tokens (User Login)

```bash
# 1. Login
LOGIN_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo-corp.com", "password": "password123"}')

# 2. Extract token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# 3. Use token
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "count": 10}'
```

### API Keys (Server-to-Server)

```bash
# 1. Get API key from seed output or create one:
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "permissions": ["read", "write"]}'

# 2. Use API key (save the 'key' field from response)
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "count": 10}'
```

## Testing Rate Limiting

```bash
# Make rapid requests to trigger rate limit
for i in {1..1100}; do
  curl -X POST http://localhost:8000/api/v1/recommendations \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "user'$i'", "count": 5}' &
done

# You should see 429 (Too Many Requests) responses after 1000 requests/minute
```

## Common API Calls

### Track Interaction
```bash
curl -X POST http://localhost:8000/api/v1/interactions \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "item_id": "item456",
    "interaction_type": "purchase"
  }'
```

### Upload Items
```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_id": "item_001",
        "title": "Amazing Product",
        "description": "Best product ever",
        "category": "electronics",
        "tags": ["gadget", "tech"]
      }
    ]
  }'
```

### Get Usage Stats
```bash
curl -X GET http://localhost:8000/api/v1/usage \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### List API Keys
```bash
curl -X GET http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Admin API

### Create Tenant
```bash
curl -X POST http://localhost:8000/api/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Company",
    "slug": "new-company",
    "plan": "starter"
  }'
```

### List Tenants
```bash
curl -X GET http://localhost:8000/api/admin/tenants
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

### View in Grafana
Open http://localhost:3001 (admin/admin)

## Running Tests

```bash
# Unit tests
uv run pytest tests/unit

# Integration tests
uv run pytest tests/integration

# All tests with coverage
uv run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uv run uvicorn src.main:app --port 8001
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql postgresql://embeddings:embeddings_pass@localhost:5432/embeddings_saas
```

### Redis Connection Error
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli ping
```

### Migration Errors
```bash
# Reset database (WARNING: destroys all data)
uv run alembic downgrade base
uv run alembic upgrade head
uv run python scripts/seed_data.py
```

## Next Steps

1. **Read the API Docs**: http://localhost:8000/docs
2. **Check the README**: Full documentation in README.md
3. **Explore the Code**: Start with `src/main.py`
4. **Write Tests**: Add tests in `tests/`
5. **Deploy**: See deployment docs in `infrastructure/`

## Default Credentials

After seeding:
- **Admin User**: admin@demo-corp.com / password123
- **Developer User**: developer@demo-corp.com / dev123
- **API Keys**: Shown in seed script output

## Need Help?

- Check logs: `docker-compose logs -f backend-api`
- View metrics: http://localhost:8000/metrics
- API docs: http://localhost:8000/docs
- Contact: platform-team@example.com
