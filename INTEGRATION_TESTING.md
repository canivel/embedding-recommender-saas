# Integration Testing Guide - Embedding Recommender SaaS

This guide provides a complete end-to-end testing workflow for the entire platform.

---

## Overview

The platform consists of **7 microservices** across **3 waves**:

**Wave 1 (Infrastructure):**
- Control Plane (Airflow)
- Observability (Prometheus, Grafana, Loki, Jaeger)
- Data Pipeline (Kafka, Spark, MinIO)

**Wave 2 (Core Services):**
- Backend API (FastAPI)
- ML Engine (LightGCN)

**Wave 3 (Frontend):**
- Customer Frontend (Next.js)
- Admin Back Office (Next.js)

---

## Prerequisites

- Docker Desktop running (8GB+ RAM allocated)
- 10GB free disk space
- Ports available: 3000, 3001, 3002, 5432, 6379, 8000, 8001, 8002, 8080, 9000, 9001, 9090, 16686

---

## Phase 1: Infrastructure Services (Wave 1)

### 1.1 Start Infrastructure

```bash
# Start all infrastructure services
docker-compose up -d postgres redis kafka zookeeper minio prometheus grafana loki jaeger airflow-webserver airflow-scheduler
```

### 1.2 Verify PostgreSQL

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Connect to database
docker-compose exec postgres psql -U embeddings -d embeddings_db

# Expected: Connected successfully
```

### 1.3 Initialize MinIO

```bash
# Run initialization script
bash scripts/init-minio.sh

# Verify buckets created
# Open http://localhost:9001 (minioadmin / minioadmin)
# Expected: 5 buckets visible
```

### 1.4 Initialize Kafka

```bash
# Run initialization script
bash scripts/init-kafka.sh

# Verify topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Expected: 12 topics listed
```

### 1.5 Verify Observability Stack

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# Check Grafana (login: admin/admin)
open http://localhost:3001

# Check Jaeger
open http://localhost:16686
```

### 1.6 Verify Airflow

```bash
# Check Airflow webserver
curl http://localhost:8080/health

# Login to Airflow (admin/admin)
open http://localhost:8080

# Expected: 2 DAGs visible
# - tenant_model_training
# - data_quality_check
```

**Wave 1 Checklist:**
- [ ] PostgreSQL accepting connections
- [ ] Redis responding
- [ ] Kafka topics created (12 topics)
- [ ] MinIO buckets created (5 buckets)
- [ ] Prometheus scraping targets
- [ ] Grafana accessible with dashboards
- [ ] Jaeger tracing enabled
- [ ] Airflow DAGs loaded

---

## Phase 2: Core Services (Wave 2)

### 2.1 Start Data Pipeline

```bash
# Start data pipeline
docker-compose up -d data-pipeline

# Check health
curl http://localhost:8002/health
# Expected: {"status":"healthy"}

# Generate sample data
cd data-pipeline
uv sync
python generate_sample_data.py --upload

# Expected: 10K users, 5K items, 100K interactions uploaded
```

### 2.2 Start Backend API

```bash
# Start backend API
docker-compose up -d backend-api

# Check health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Run database migrations
docker-compose exec backend-api alembic upgrade head

# View API documentation
open http://localhost:8000/docs
```

### 2.3 Create Test Tenant

```bash
# Create a demo tenant
curl -X POST http://localhost:8000/api/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo E-commerce",
    "slug": "demo-ecommerce",
    "email": "admin@demo-ecommerce.com"
  }'

# Expected: 201 Created with tenant_id
```

### 2.4 Start ML Engine

```bash
# Start ML engine
docker-compose up -d ml-engine

# Check health
curl http://localhost:8001/health
# Expected: {"status":"healthy"}

# Trigger model training (via Airflow)
# Go to http://localhost:8080
# Trigger "tenant_model_training" DAG with config:
# {"tenant_id": "demo-ecommerce"}

# Monitor training progress in Airflow logs
```

### 2.5 Test Recommendation Flow

```bash
# After model training completes (~5-10 minutes)

# Get authentication token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo-ecommerce.com", "password": "changeme"}' \
  | jq -r '.access_token')

# Get recommendations for a user
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "count": 10
  }'

# Expected: 10 recommended items with scores
```

**Wave 2 Checklist:**
- [ ] Data Pipeline accepting uploads
- [ ] Sample data generated successfully
- [ ] Backend API responding
- [ ] Database migrations applied
- [ ] Tenant created
- [ ] ML Engine responding
- [ ] Model training completes successfully
- [ ] Recommendations returned with valid scores
- [ ] FAISS index built and loaded

---

## Phase 3: Frontend Applications (Wave 3)

### 3.1 Start Customer Frontend

```bash
# Start customer frontend
docker-compose up -d frontend

# Or run locally for development
cd frontend
npm install
npm run dev

# Access frontend
open http://localhost:3000
```

### 3.2 Test Customer Frontend

**Login Flow:**
1. Navigate to http://localhost:3000
2. Click "Sign Up" and create account
3. Or login with demo account (admin@demo-corp.com / password123)
4. Expected: Redirected to dashboard

**Dashboard:**
1. View metrics cards (API calls, recommendations, cache hits)
2. Check usage charts
3. View recent activity feed
4. Expected: Data loads without errors

**Data Upload:**
1. Navigate to "Data" page
2. Drag and drop CSV file or click to browse
3. Expected: File uploads, validation runs, success message

**API Keys:**
1. Navigate to "API Keys" page
2. Click "Create New API Key"
3. Copy the generated key
4. Expected: Key created and listed

**Analytics:**
1. Navigate to "Analytics" page
2. View performance charts
3. Change date range
4. Expected: Charts update dynamically

**Settings:**
1. Navigate to "Settings" page
2. Update profile information
3. Save changes
4. Expected: Settings saved successfully

### 3.3 Start Admin Back Office

```bash
# Start back office
docker-compose up -d backoffice

# Or run locally
cd backoffice
npm install
npm run dev

# Access back office
open http://localhost:3002
```

### 3.4 Test Admin Back Office

**Login:**
1. Navigate to http://localhost:3002
2. Login with: admin@acme.com / admin123
3. Expected: Redirected to admin dashboard

**Dashboard:**
1. View system KPIs (tenants, API calls, alerts)
2. Check trend charts
3. View active alerts
4. Expected: System overview loads

**Tenant Management:**
1. Navigate to "Tenants" page
2. View tenant list
3. Click a tenant to view details
4. Expected: Tenant details load with charts

**Create Tenant:**
1. Click "Create Tenant"
2. Fill in: Name, Slug, Email
3. Submit form
4. Expected: Tenant created, redirected to details

**Suspend Tenant:**
1. In tenant details, click "Suspend"
2. Confirm action
3. Expected: Tenant suspended, status updated

**Model Management:**
1. Navigate to "Models" page
2. View model versions
3. Deploy a model with traffic percentage
4. Expected: Model deployed successfully

**Support Dashboard:**
1. Navigate to "Support" page
2. View tenant health scores
3. Use impersonation tool (logged in audit)
4. Expected: Can view tenant's perspective

**Monitoring:**
1. Navigate to "Monitoring" page
2. View service health status
3. Check performance metrics
4. Expected: All services green

**Audit Logs:**
1. Navigate to "Audit Logs" page
2. Search for specific actions
3. Export to CSV
4. Expected: Logs displayed and exportable

**Wave 3 Checklist:**
- [ ] Customer Frontend loads
- [ ] Authentication works
- [ ] Dashboard shows metrics
- [ ] Data upload functions
- [ ] API key creation works
- [ ] Analytics charts render
- [ ] Settings save successfully
- [ ] Admin Back Office loads
- [ ] Tenant CRUD operations work
- [ ] Model management functions
- [ ] Monitoring displays correctly
- [ ] Audit logs captured
- [ ] Impersonation tracked

---

## Phase 4: End-to-End Scenario

### Complete User Journey

**Scenario: E-commerce company "TechGadgets" onboards to platform**

#### Step 1: Admin Creates Tenant (Back Office)

```bash
# Login to back office
open http://localhost:3002
# Login: admin@acme.com / admin123

# Create tenant
# Name: TechGadgets
# Slug: techgadgets
# Email: admin@techgadgets.com
```

#### Step 2: Customer Onboards (Frontend)

```bash
# Customer receives invitation email (simulated)
# Access frontend
open http://localhost:3000

# Sign up with email: admin@techgadgets.com
# Set password
# Login
```

#### Step 3: Upload Product Catalog

```bash
# In customer frontend, go to "Data" page
# Upload CSV with columns: item_id, title, category, price, image_url
# Sample: 1000 tech products

# Verify upload in data-pipeline logs
docker-compose logs data-pipeline

# Expected: Data validated and stored in MinIO
```

#### Step 4: Upload User Interactions

```bash
# Upload interactions CSV: user_id, item_id, interaction_type, timestamp
# Sample: 50K user interactions (views, clicks, purchases)

# Verify in Kafka
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_interactions \
  --from-beginning \
  --max-messages 10

# Expected: Events flowing through Kafka
```

#### Step 5: Train Recommendation Model

```bash
# Option A: Via Airflow UI
open http://localhost:8080
# Trigger "tenant_model_training" DAG
# Config: {"tenant_id": "techgadgets"}

# Option B: Via Backend API
curl -X POST http://localhost:8000/api/admin/train \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "techgadgets"}'

# Monitor progress in Airflow logs
# Expected: Training completes in ~5-10 minutes
# NDCG@10 > 0.30
```

#### Step 6: Deploy Model (Back Office)

```bash
# In back office, go to "Models" page
# Find latest model version for techgadgets
# Click "Deploy" with 100% traffic
# Expected: Model deployed, FAISS index built
```

#### Step 7: Test Recommendations (Frontend)

```bash
# In customer frontend, go to "Test" page
# Enter user_id: user_123
# Click "Get Recommendations"
# Expected: 10 product recommendations with scores
```

#### Step 8: Create API Key (Frontend)

```bash
# In customer frontend, go to "API Keys" page
# Click "Create API Key"
# Name: "Production - Website"
# Copy key
```

#### Step 9: Integrate API (Customer's Application)

```bash
# Use copied API key
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "count": 5,
    "filters": {"category": "smartphones"}
  }'

# Expected: Filtered recommendations returned
```

#### Step 10: Monitor Performance (Back Office)

```bash
# In back office, go to "Monitoring" page
# View API latency, throughput, errors
# Check Grafana dashboards
open http://localhost:3001
# Dashboard: "API Performance"
# Expected: Metrics showing API calls, latency p95 < 100ms
```

#### Step 11: View Analytics (Frontend)

```bash
# In customer frontend, go to "Analytics" page
# View:
# - Recommendations served
# - Click-through rate
# - Conversion rate
# - Popular items
# Expected: Charts populated with data
```

#### Step 12: Audit Trail (Back Office)

```bash
# In back office, go to "Audit Logs" page
# Filter by tenant: techgadgets
# Expected: All actions logged:
# - Tenant creation
# - Data uploads
# - Model training
# - Model deployment
# - API key creation
```

**End-to-End Checklist:**
- [ ] Tenant created successfully
- [ ] Customer can sign up and login
- [ ] Product data uploaded
- [ ] User interactions ingested
- [ ] Model training completes
- [ ] Model deployed to production
- [ ] Recommendations working
- [ ] API key generated
- [ ] External API integration works
- [ ] Monitoring shows metrics
- [ ] Analytics display data
- [ ] Audit trail complete

---

## Phase 5: Performance Testing

### 5.1 Load Testing Setup

```bash
# Install k6 (load testing tool)
# macOS
brew install k6

# Or download from https://k6.io/

# Create load test script
cat > load-test.js <<EOF
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 50 },  // Ramp up to 50 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
};

export default function () {
  let res = http.post('http://localhost:8000/api/v1/recommendations',
    JSON.stringify({
      user_id: 'user_' + Math.floor(Math.random() * 10000),
      count: 10
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer <your-api-key>'
      }
    }
  );

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 100ms': (r) => r.timings.duration < 100,
  });

  sleep(1);
}
EOF

# Run load test
k6 run load-test.js
```

### 5.2 Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| API Latency (p95) | < 100ms | < 200ms |
| FAISS Search | < 20ms | < 50ms |
| Throughput | > 100 req/s | > 50 req/s |
| Error Rate | < 1% | < 5% |
| Cache Hit Rate | > 80% | > 60% |

### 5.3 Monitor Performance

```bash
# Check Grafana during load test
open http://localhost:3001
# Dashboard: "API Performance"

# Watch for:
# - Latency staying below 100ms
# - No error spikes
# - Cache hit rate > 80%
# - CPU/memory stable
```

**Performance Checklist:**
- [ ] API handles 50+ concurrent users
- [ ] p95 latency < 100ms
- [ ] Error rate < 1%
- [ ] Cache hit rate > 80%
- [ ] No memory leaks (run for 1 hour)
- [ ] Database connection pool stable
- [ ] Redis not overwhelmed

---

## Phase 6: Failure Scenarios

### 6.1 Database Failure

```bash
# Stop PostgreSQL
docker-compose stop postgres

# Test API behavior
curl http://localhost:8000/health
# Expected: Returns error but doesn't crash

# Check logs
docker-compose logs backend-api
# Expected: Connection errors logged, not exceptions

# Restart PostgreSQL
docker-compose start postgres

# Expected: Services auto-recover
```

### 6.2 Redis Failure

```bash
# Stop Redis
docker-compose stop redis

# Test recommendations
# Expected: Still works, but no caching (slower)

# Restart Redis
docker-compose start redis

# Expected: Cache resumes
```

### 6.3 ML Engine Failure

```bash
# Stop ML Engine
docker-compose stop ml-engine

# Request recommendations
# Expected: Fallback to popular items or error message

# Restart ML Engine
docker-compose start ml-engine
```

### 6.4 Kafka Failure

```bash
# Stop Kafka
docker-compose stop kafka

# Upload data
# Expected: API queues events, retries

# Restart Kafka
docker-compose start kafka

# Expected: Queued events processed
```

**Failure Recovery Checklist:**
- [ ] Services gracefully handle database outage
- [ ] Cache failure doesn't break recommendations
- [ ] ML Engine failure has fallback
- [ ] Kafka failure buffers events
- [ ] All services auto-recover on restart
- [ ] No data loss during failures
- [ ] Alerts triggered in Grafana

---

## Phase 7: Security Testing

### 7.1 Authentication

```bash
# Test without token
curl http://localhost:8000/api/v1/recommendations
# Expected: 401 Unauthorized

# Test with invalid token
curl -H "Authorization: Bearer invalid" \
  http://localhost:8000/api/v1/recommendations
# Expected: 401 Unauthorized

# Test with expired token
# (Use token from > 15 minutes ago)
# Expected: 401 Unauthorized, prompt to refresh
```

### 7.2 Authorization

```bash
# Test tenant isolation
# Login as tenant A, try to access tenant B's data
# Expected: 403 Forbidden
```

### 7.3 Rate Limiting

```bash
# Send 100 requests rapidly
for i in {1..100}; do
  curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/recommendations \
    -d '{"user_id":"user_123","count":10}' &
done

# Expected: Some requests return 429 Too Many Requests
```

### 7.4 SQL Injection

```bash
# Test with malicious input
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer <token>" \
  -d '{"user_id":"'; DROP TABLE users; --","count":10}'

# Expected: Input sanitized, no error, no database damage
```

**Security Checklist:**
- [ ] All endpoints require authentication
- [ ] Tenant isolation enforced
- [ ] Rate limiting works
- [ ] SQL injection prevented
- [ ] XSS protection enabled
- [ ] CORS configured correctly
- [ ] Secrets not exposed in logs
- [ ] Audit logs capture all actions

---

## Phase 8: Final Validation

### 8.1 Complete System Health Check

```bash
# Run comprehensive health check
bash scripts/health-check.sh

# Or manually check all services
curl http://localhost:8000/health  # Backend API
curl http://localhost:8001/health  # ML Engine
curl http://localhost:8002/health  # Data Pipeline
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:8080/health  # Airflow

# All should return healthy status
```

### 8.2 Verify All Dashboards

```bash
# Grafana dashboards
open http://localhost:3001
# Login: admin/admin
# Check:
# - System Health (all green)
# - API Performance (metrics flowing)
# - ML Engine (training jobs visible)
# - Business Metrics (data populated)

# Jaeger traces
open http://localhost:16686
# Search for recent traces
# Expected: Request traces visible

# Airflow
open http://localhost:8080
# Check:
# - Both DAGs enabled
# - Recent successful runs
# - No failed tasks
```

### 8.3 Data Integrity

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U embeddings -d embeddings_db

# Check tables
\dt

# Count records
SELECT COUNT(*) FROM tenants;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM api_keys;

# Expected: Data present and accurate
```

### 8.4 Backup & Recovery

```bash
# Backup database
docker-compose exec postgres pg_dump -U embeddings embeddings_db > backup.sql

# Backup MinIO data
# Access MinIO console: http://localhost:9001
# Download buckets

# Test restore (on separate instance)
docker-compose exec postgres psql -U embeddings -d embeddings_db < backup.sql
```

**Final Validation Checklist:**
- [ ] All 17 services running
- [ ] All health checks passing
- [ ] Grafana dashboards populated
- [ ] Jaeger traces visible
- [ ] Airflow DAGs successful
- [ ] Database tables populated
- [ ] MinIO buckets contain data
- [ ] Kafka topics have messages
- [ ] Frontend loads without errors
- [ ] Back office loads without errors
- [ ] End-to-end flow works
- [ ] Backups can be restored

---

## Troubleshooting

### Common Issues

**Port Conflicts:**
```bash
# Check what's using a port
netstat -an | grep <port>

# Kill process
kill -9 <pid>
```

**Container Won't Start:**
```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild image
docker-compose build --no-cache <service-name>
docker-compose up -d <service-name>
```

**Database Connection Errors:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose exec backend-api alembic upgrade head
```

**Out of Memory:**
```bash
# Check Docker memory
docker stats

# Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Memory (8GB+)

# Restart Docker
```

**Kafka Topics Not Created:**
```bash
# Recreate topics
bash scripts/init-kafka.sh

# Verify
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

## Continuous Integration

### GitHub Actions Workflows

After pushing to GitHub, the following CI workflows will run automatically:

1. **Backend API CI** (`.github/workflows/backend-api.yml`)
   - Tests on every PR
   - Builds Docker image on merge to main

2. **ML Engine CI** (`.github/workflows/ml-engine.yml`)
   - Tests model training
   - Validates FAISS index building

3. **Data Pipeline CI** (`.github/workflows/data-pipeline.yml`)
   - Tests ETL pipelines
   - Validates Kafka integration

4. **Frontend CI** (`.github/workflows/frontend.yml`)
   - Builds Next.js app
   - Runs linting

### Manual CI Run

```bash
# Install GitHub CLI
gh auth login

# Trigger workflow
gh workflow run backend-api.yml
gh workflow run ml-engine.yml
gh workflow run data-pipeline.yml
gh workflow run frontend.yml
```

---

## Next Steps

After successful integration testing:

1. **Performance Tuning**
   - Optimize database queries
   - Tune cache settings
   - Adjust rate limits

2. **Production Deployment**
   - Set up Kubernetes cluster
   - Configure auto-scaling
   - Enable SSL/TLS

3. **Monitoring Setup**
   - Configure PagerDuty alerts
   - Set up Slack notifications
   - Create runbooks

4. **Customer Onboarding**
   - Onboard first beta customer
   - Gather feedback
   - Iterate on features

---

## Success Criteria

Integration testing is considered **COMPLETE** when:

- ✅ All services start without errors
- ✅ End-to-end user journey works
- ✅ Performance meets targets
- ✅ Failure scenarios handled gracefully
- ✅ Security tests pass
- ✅ All dashboards show data
- ✅ Load testing successful
- ✅ Data integrity verified
- ✅ Backups/restore working

---

**Integration testing completed?** Proceed to production deployment following `infrastructure/kubernetes/` guides.
