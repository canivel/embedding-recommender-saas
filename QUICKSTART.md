# Quick Start Guide - Embedding Recommender SaaS Platform

## 🚀 Get Started in 5 Minutes

This guide will help you run the entire platform locally using Docker Compose.

## Prerequisites

- Docker Desktop installed and running
- At least 8GB RAM available for Docker
- 10GB free disk space

## Step 1: Clone and Setup

```bash
cd c:\Users\dcani\projects\general-embedding-recommender-saas

# Copy environment file
cp .env.example .env

# Make scripts executable (if on Unix/Mac)
chmod +x scripts/*.sh
```

## Step 2: Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, Kafka, MinIO, and Observability stack
docker-compose up -d postgres redis kafka zookeeper minio prometheus grafana loki jaeger
```

Wait for services to be healthy (~30 seconds):

```bash
docker-compose ps
```

## Step 3: Initialize Infrastructure

```bash
# Initialize MinIO buckets
bash scripts/init-minio.sh

# Initialize Kafka topics
bash scripts/init-kafka.sh
```

## Step 4: Start Application Services

```bash
# Start backend API
docker-compose up -d backend-api

# Start ML Engine
docker-compose up -d ml-engine

# Start Data Pipeline
docker-compose up -d data-pipeline

# Start Frontend
docker-compose up -d frontend

# Start Back Office
docker-compose up -d backoffice

# Start Airflow
docker-compose up -d airflow-webserver airflow-scheduler
```

## Step 5: Verify All Services

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f backend-api
```

## Step 6: Access the Platform

### Customer Dashboard
🌐 **URL**: http://localhost:3000

**Demo Account**:
- Email: `admin@demo-corp.com`
- Password: `password123`

### Admin Back Office
🔧 **URL**: http://localhost:3002

**Demo Account**:
- Email: `admin@internal.com`
- Password: `admin123`

### API Documentation
📚 **URL**: http://localhost:8000/docs

**Test API**:
```bash
curl http://localhost:8000/health
```

### Monitoring & Observability

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | None |
| **Jaeger** | http://localhost:16686 | None |
| **Airflow** | http://localhost:8080 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |

## Step 7: Load Sample Data

```bash
# Generate and upload sample e-commerce data
cd data-pipeline
uv sync
python generate_sample_data.py --upload
```

This creates:
- 10,000 users
- 5,000 products (electronics)
- 100,000 interactions (views, clicks, purchases)

## Step 8: Train Your First Model

### Option A: Via Airflow UI
1. Go to http://localhost:8080
2. Login (admin/admin)
3. Find `tenant_model_training` DAG
4. Click "Trigger DAG"
5. Add config: `{"tenant_id": "demo"}`
6. Monitor progress

### Option B: Via CLI
```bash
# Trigger training via API
curl -X POST http://localhost:8000/api/admin/train \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "demo"}'
```

## Step 9: Get Recommendations

```bash
# Login to get access token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo-corp.com", "password": "password123"}' \
  | jq -r '.access_token')

# Get recommendations
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "count": 10,
    "filters": {"category": "electronics"}
  }'
```

## Step 10: Explore Dashboards

### Grafana Dashboards
1. Go to http://localhost:3001
2. Login (admin/admin)
3. Navigate to Dashboards → Browse
4. Explore:
   - System Health
   - API Performance
   - ML Engine Metrics
   - Business Metrics

### Customer Dashboard
1. Go to http://localhost:3000
2. Login with demo account
3. Explore:
   - Dashboard (usage overview)
   - Data Upload (upload your CSV)
   - API Keys (create test keys)
   - Analytics (view metrics)

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend-api
docker-compose logs -f ml-engine
docker-compose logs -f data-pipeline
```

### Restart Service
```bash
docker-compose restart backend-api
```

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Fresh Start)
```bash
docker-compose down -v
```

### Check Service Health
```bash
curl http://localhost:8000/health  # Backend API
curl http://localhost:8001/health  # ML Engine
curl http://localhost:8002/health  # Data Pipeline
```

## Troubleshooting

### Services Won't Start

**Check Docker Resources**:
- Ensure Docker has at least 8GB RAM allocated
- Check CPU allocation (4+ cores recommended)

**Check Ports**:
```bash
# Check if ports are already in use
netstat -an | grep 8000
netstat -an | grep 5432
netstat -an | grep 6379
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### MinIO Buckets Not Created

```bash
# Re-run initialization
bash scripts/init-minio.sh

# Verify buckets exist
# Go to http://localhost:9001 (minioadmin/minioadmin)
```

### Kafka Topics Not Created

```bash
# Re-run initialization
bash scripts/init-kafka.sh

# Verify topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Model Training Fails

```bash
# Check ML Engine logs
docker-compose logs ml-engine

# Check Airflow logs
docker-compose logs airflow-scheduler

# Verify training data exists
# Go to MinIO Console: http://localhost:9001
# Check bucket: embeddings-training-data
```

### Frontend Can't Connect to Backend

**Check Backend is Running**:
```bash
curl http://localhost:8000/health
```

**Check CORS Configuration**:
- Backend should allow `http://localhost:3000` origin
- See `backend-api/src/main.py` CORS middleware

### Out of Memory

**Increase Docker Memory**:
1. Open Docker Desktop
2. Settings → Resources
3. Increase Memory to 8GB+
4. Apply & Restart

**Reduce Services**:
```bash
# Run only essential services
docker-compose up -d postgres redis minio backend-api ml-engine
```

## Performance Tips

### For Development

**Use Volume Mounts for Hot Reload**:
```yaml
# In docker-compose.yml
volumes:
  - ./backend-api:/app
command: uvicorn src.main:app --reload
```

**Disable Unnecessary Services**:
```bash
# Don't need Jaeger/Loki during development
docker-compose up -d postgres redis kafka minio backend-api ml-engine frontend
```

### For Production Testing

**Enable All Monitoring**:
```bash
docker-compose up -d
```

**Use Production Build**:
```bash
# Build optimized images
docker-compose build --no-cache

# Run with production settings
docker-compose up -d
```

## Next Steps

1. **Read the Documentation**:
   - [Development Roadmap](docs/DEVELOPMENT_ROADMAP.md)
   - [System Overview](docs/architecture/SYSTEM_OVERVIEW.md)
   - [API Contracts](docs/api-contracts/API_CONTRACTS.md)

2. **Explore Components**:
   - [Backend API](backend-api/README.md)
   - [ML Engine](ml-engine/README.md)
   - [Data Pipeline](data-pipeline/README.md)
   - [Control Plane](control-plane/README.md)
   - [Observability](observability/README.md)

3. **Run End-to-End Example**:
   - See [END_TO_END_EXAMPLE.md](END_TO_END_EXAMPLE.md)

4. **Customize for Your Use Case**:
   - Upload your own data
   - Train custom models
   - Integrate with your application

## Support

- **Documentation**: See [docs/](docs/)
- **Issues**: Create GitHub issue
- **Questions**: See README.md

---

**Congratulations! You now have a complete recommendation system running locally.** 🎉
