# End-to-End Example: E-Commerce Recommendation System

This guide walks you through a complete example of setting up and using the Embedding Recommender SaaS platform for an e-commerce business.

## Scenario: "TechGadgets Store"

**Business Context**:
- Online electronics retailer
- 5,000 products (smartphones, laptops, accessories)
- 10,000 registered customers
- 100,000 historical purchases/views
- Goal: Increase sales with personalized product recommendations

## Part 1: Setup & Data Loading (15 minutes)

### Step 1.1: Start the Platform

```bash
# Navigate to project
cd c:\Users\dcani\projects\general-embedding-recommender-saas

# Start all services
docker-compose up -d

# Wait for services to be healthy (check with)
docker-compose ps
```

**Expected Output**:
```
NAME                    STATUS              PORTS
postgres                Up (healthy)        5432->5432
redis                   Up (healthy)        6379->6379
kafka                   Up (healthy)        9092->9092
minio                   Up (healthy)        9000->9000, 9001->9001
backend-api             Up (healthy)        8000->8000
ml-engine               Up (healthy)        8001->8001
data-pipeline           Up (healthy)        8002->8002
frontend                Up                  3000->3000
grafana                 Up                  3001->3000
prometheus              Up                  9090->9090
airflow-webserver       Up                  8080->8080
```

### Step 1.2: Initialize Infrastructure

```bash
# Create S3 buckets
bash scripts/init-minio.sh

# Create Kafka topics
bash scripts/init-kafka.sh
```

### Step 1.3: Create Tenant Account

```bash
# Create TechGadgets tenant
curl -X POST http://localhost:8000/api/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechGadgets Store",
    "slug": "techgadgets",
    "plan": "pro",
    "settings": {
      "default_model": "lightgcn",
      "embedding_dimension": 64
    }
  }'
```

**Response**:
```json
{
  "id": "tenant_123",
  "name": "TechGadgets Store",
  "slug": "techgadgets",
  "plan": "pro",
  "status": "active",
  "created_at": "2025-01-07T10:00:00Z"
}
```

### Step 1.4: Create User Account

```bash
curl -X POST http://localhost:8000/api/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_123",
    "email": "admin@techgadgets.com",
    "password": "SecurePass123!",
    "role": "admin"
  }'
```

### Step 1.5: Generate Sample Data

```bash
cd data-pipeline

# Install dependencies
uv sync

# Generate realistic e-commerce data
python generate_sample_data.py \
  --users 10000 \
  --items 5000 \
  --interactions 100000 \
  --output sample_data/
```

**Generated Files**:
- `sample_data/items.csv` - 5,000 products
- `sample_data/interactions.csv` - 100,000 user interactions
- `sample_data/users.csv` - 10,000 users (optional)

**Sample items.csv**:
```csv
item_id,title,category,price,brand,description
item_0001,iPhone 15 Pro,Smartphones,999.99,Apple,Latest flagship smartphone
item_0002,MacBook Pro,Laptops,2499.99,Apple,Professional laptop for creators
item_0003,AirPods Pro,Audio,249.99,Apple,Wireless earbuds with ANC
item_0004,Galaxy S24,Smartphones,899.99,Samsung,Android flagship phone
item_0005,Dell XPS 13,Laptops,1299.99,Dell,Ultraportable laptop
```

**Sample interactions.csv**:
```csv
user_id,item_id,interaction_type,timestamp,rating
user_0001,item_0001,purchase,2025-01-01T10:30:00Z,5.0
user_0001,item_0003,view,2025-01-01T10:25:00Z,
user_0002,item_0002,purchase,2025-01-01T11:00:00Z,5.0
user_0002,item_0005,click,2025-01-01T10:55:00Z,
user_0003,item_0001,view,2025-01-01T12:00:00Z,
```

### Step 1.6: Upload Data

#### Option A: Via Web Interface

1. Open http://localhost:3000
2. Login: `admin@techgadgets.com` / `SecurePass123!`
3. Navigate to **Data** tab
4. Upload `items.csv` (Products)
5. Upload `interactions.csv` (User Interactions)

#### Option B: Via API

```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@techgadgets.com", "password": "SecurePass123!"}' \
  | jq -r '.access_token')

# Upload products
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_data/items.csv"

# Upload interactions
curl -X POST "http://localhost:8000/api/v1/interactions" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_data/interactions.csv"
```

**Response**:
```json
{
  "status": "success",
  "accepted": 5000,
  "rejected": 0,
  "validation_errors": []
}
```

### Step 1.7: Verify Data Upload

```bash
# Check MinIO Console
open http://localhost:9001  # minioadmin/minioadmin

# Navigate to bucket: embeddings-raw-data/tenant_123/
# You should see:
# - items/2025-01-07/items.parquet
# - interactions/2025-01-07/interactions.parquet
```

---

## Part 2: Train Recommendation Model (30 minutes)

### Step 2.1: Trigger Model Training

#### Option A: Via Airflow UI

1. Open http://localhost:8080 (admin/admin)
2. Find `tenant_model_training` DAG
3. Click **Trigger DAG** (play button)
4. Add configuration:
   ```json
   {
     "tenant_id": "tenant_123",
     "model_type": "lightgcn",
     "embedding_dim": 64,
     "num_layers": 3,
     "epochs": 20
   }
   ```
5. Click **Trigger**
6. Monitor progress in Graph View

#### Option B: Via API

```bash
curl -X POST http://localhost:8000/api/admin/training/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_123",
    "model_type": "lightgcn",
    "config": {
      "embedding_dim": 64,
      "num_layers": 3,
      "epochs": 20,
      "learning_rate": 0.001,
      "batch_size": 1024
    }
  }'
```

**Response**:
```json
{
  "job_id": "job_456",
  "status": "queued",
  "estimated_duration_minutes": 30,
  "started_at": null
}
```

### Step 2.2: Monitor Training Progress

```bash
# Check job status
curl -X GET http://localhost:8000/api/admin/training/status/job_456 \
  -H "Authorization: Bearer $TOKEN"
```

**Response (running)**:
```json
{
  "job_id": "job_456",
  "status": "running",
  "progress": 45,
  "current_epoch": 9,
  "total_epochs": 20,
  "metrics": {
    "train_loss": 0.234,
    "val_ndcg_10": 0.312
  }
}
```

**Response (completed)**:
```json
{
  "job_id": "job_456",
  "status": "completed",
  "progress": 100,
  "metrics": {
    "train_loss": 0.156,
    "val_ndcg_10": 0.378,
    "val_precision_10": 0.234,
    "val_recall_10": 0.456,
    "training_time_seconds": 1842
  },
  "model_path": "s3://embeddings-models/tenant_123/lightgcn_v1.pth",
  "index_path": "s3://embeddings-indices/tenant_123/faiss_v1.bin"
}
```

### Step 2.3: Verify Model Deployment

```bash
# Check ML Engine health
curl http://localhost:8001/health
```

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "lightgcn_v1",
  "index_loaded": true,
  "index_size": 5000,
  "cache_connected": true
}
```

### Step 2.4: View Training Metrics in Grafana

1. Open http://localhost:3001 (admin/admin)
2. Go to **Dashboards** → **ML Engine**
3. View:
   - Training job status: ✅ Completed
   - Model quality: NDCG@10 = 0.378
   - Training duration: ~30 minutes
   - Model version: lightgcn_v1

---

## Part 3: Get Recommendations (5 minutes)

### Step 3.1: Get Recommendations via API

```bash
# Get recommendations for user_0001
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_0001",
    "count": 10,
    "filters": {
      "category": "Electronics"
    }
  }'
```

**Response**:
```json
{
  "recommendations": [
    {
      "item_id": "item_2345",
      "title": "Sony WH-1000XM5",
      "score": 0.92,
      "category": "Audio",
      "price": 399.99,
      "reason": "Based on your interest in premium audio"
    },
    {
      "item_id": "item_1234",
      "title": "iPad Pro 12.9",
      "score": 0.89,
      "category": "Tablets",
      "price": 1099.99,
      "reason": "Customers who bought iPhone also purchased this"
    },
    {
      "item_id": "item_3456",
      "title": "Apple Watch Series 9",
      "score": 0.87,
      "category": "Wearables",
      "price": 429.99,
      "reason": "Complements your Apple ecosystem"
    }
  ],
  "metadata": {
    "model_version": "lightgcn_v1",
    "latency_ms": 45,
    "cache_hit": true,
    "algorithm": "lightgcn"
  }
}
```

### Step 3.2: Test Different Scenarios

**Scenario A: New User (Cold Start)**
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "user_new",
    "count": 10
  }'
```

**Response**: Returns popular items (fallback strategy)

**Scenario B: Category Filtering**
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "user_0001",
    "count": 10,
    "filters": {
      "category": "Laptops",
      "min_price": 1000,
      "max_price": 2000
    }
  }'
```

**Scenario C: Exclude Already Purchased**
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "user_0001",
    "count": 10,
    "filters": {
      "exclude_ids": ["item_0001", "item_0003"]
    }
  }'
```

### Step 3.3: Track User Interaction

```bash
# User viewed a recommended product
curl -X POST http://localhost:8000/api/v1/interactions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "user_0001",
    "item_id": "item_2345",
    "interaction_type": "click",
    "context": {
      "source": "recommendations",
      "position": 1
    }
  }'

# User purchased the product
curl -X POST http://localhost:8000/api/v1/interactions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "user_0001",
    "item_id": "item_2345",
    "interaction_type": "purchase",
    "context": {
      "source": "recommendations",
      "revenue": 399.99
    }
  }'
```

---

## Part 4: Integration with Your Application (10 minutes)

### Step 4.1: Create API Key

```bash
# Create production API key
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Production - Website",
    "permissions": ["read", "write"]
  }'
```

**Response**:
```json
{
  "id": "key_789",
  "name": "Production - Website",
  "key": "your_api_key_here_abc123def456ghi789jkl012mno345",
  "key_prefix": "sk_live_abc",
  "created_at": "2025-01-07T15:00:00Z",
  "status": "active"
}
```

⚠️ **Important**: Copy the full API key - it's only shown once!

### Step 4.2: Integrate into Your Website

**Python Example**:
```python
import requests

API_KEY = "your_api_key_here_abc123def456ghi789jkl012mno345"
API_URL = "https://api.yourplatform.com"

def get_recommendations(user_id, count=10):
    response = requests.post(
        f"{API_URL}/api/v1/recommendations",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"user_id": user_id, "count": count}
    )
    return response.json()

# Usage
recommendations = get_recommendations("user_123", count=5)
for item in recommendations["recommendations"]:
    print(f"{item['title']}: ${item['price']} (score: {item['score']})")
```

**JavaScript Example**:
```javascript
const API_KEY = 'your_api_key_here_abc123def456ghi789jkl012mno345';
const API_URL = 'https://api.yourplatform.com';

async function getRecommendations(userId, count = 10) {
  const response = await fetch(`${API_URL}/api/v1/recommendations`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ user_id: userId, count })
  });
  return await response.json();
}

// Usage
const recommendations = await getRecommendations('user_123', 5);
recommendations.recommendations.forEach(item => {
  console.log(`${item.title}: $${item.price} (score: ${item.score})`);
});
```

**PHP Example**:
```php
<?php
$apiKey = 'your_api_key_here_abc123def456ghi789jkl012mno345';
$apiUrl = 'https://api.yourplatform.com';

function getRecommendations($userId, $count = 10) {
    global $apiKey, $apiUrl;

    $ch = curl_init("$apiUrl/api/v1/recommendations");
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        "Authorization: Bearer $apiKey",
        "Content-Type: application/json"
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'user_id' => $userId,
        'count' => $count
    ]));

    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// Usage
$recommendations = getRecommendations('user_123', 5);
foreach ($recommendations['recommendations'] as $item) {
    echo "{$item['title']}: \${$item['price']} (score: {$item['score']})\n";
}
?>
```

---

## Part 5: Monitor Performance (Ongoing)

### Step 5.1: View Business Metrics

1. Open http://localhost:3000 (Customer Dashboard)
2. Navigate to **Analytics**
3. View metrics:
   - **Recommendations Served**: 15,234 (today)
   - **Click-Through Rate**: 12.5%
   - **Conversion Rate**: 3.2%
   - **Revenue from Recommendations**: $45,678 (this month)

### Step 5.2: View Technical Metrics (Grafana)

1. Open http://localhost:3001 (admin/admin)
2. Dashboard: **API Performance**
   - Request rate: 450 req/sec
   - Latency p95: 68ms
   - Error rate: 0.02%

3. Dashboard: **ML Engine**
   - Model quality: NDCG@10 = 0.378
   - Cache hit rate: 94%
   - ANN search time: 12ms p95

4. Dashboard: **Business Metrics**
   - Active users: 8,547
   - Top products recommended
   - Revenue attribution

### Step 5.3: Set Up Alerts

Navigate to **Grafana** → **Alerting** → **Alert Rules**

**Critical Alerts**:
- Recommendation latency > 200ms
- Error rate > 1%
- Model quality drops below 0.30

**Warning Alerts**:
- Cache hit rate < 80%
- Training job failures
- Data freshness > 24 hours

---

## Part 6: Iterate and Improve (Weekly)

### Step 6.1: Retrain Model with New Data

Models should be retrained regularly as new interaction data comes in.

**Automatic Retraining** (Airflow):
- Configured to run daily at 2 AM
- Uses last 90 days of interaction data
- Automatically deploys if NDCG@10 improves

**Manual Retraining**:
```bash
# Trigger via API
curl -X POST http://localhost:8000/api/admin/training/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tenant_id": "tenant_123"}'
```

### Step 6.2: A/B Test New Models

```bash
# Create A/B test
curl -X POST http://localhost:8000/api/admin/ab-tests \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "LightGCN vs Two-Tower",
    "variants": [
      {"id": "control", "model_version": "lightgcn_v1", "traffic": 50},
      {"id": "treatment", "model_version": "two_tower_v1", "traffic": 50}
    ],
    "metric": "conversion_rate",
    "duration_days": 7
  }'
```

Monitor results in Analytics dashboard.

### Step 6.3: Analyze Top Products

```bash
# Get top recommended products
curl -X GET http://localhost:8000/api/v1/analytics/top-products?days=30 \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "top_products": [
    {
      "item_id": "item_0001",
      "title": "iPhone 15 Pro",
      "recommendation_count": 45678,
      "click_through_rate": 0.125,
      "conversion_rate": 0.032,
      "revenue": 45678.90
    }
  ]
}
```

---

## Success Metrics

After implementing recommendations, TechGadgets Store saw:

✅ **15% increase** in average order value
✅ **22% increase** in cross-sell conversions
✅ **8% reduction** in bounce rate
✅ **3.2% overall conversion rate** (up from 2.4%)
✅ **$45K additional revenue** per month from recommendations

## Common Issues & Solutions

### Low NDCG Score (<0.30)

**Possible causes**:
- Insufficient training data
- Model not trained long enough
- Poor data quality

**Solutions**:
- Ensure at least 10K interactions
- Increase epochs to 50
- Run data quality checks

### High Latency (>100ms)

**Possible causes**:
- Cache miss rate high
- FAISS index not optimized
- Too many concurrent requests

**Solutions**:
- Increase Redis TTL
- Use IVF index instead of Flat
- Scale ML Engine horizontally

### Cold-Start Not Working

**Possible causes**:
- Popular items not pre-computed
- Fallback logic not triggered

**Solutions**:
- Pre-compute popular items daily
- Check cold-start detection logic

---

## Next Steps

1. **Upload your real data** (replace sample data)
2. **Fine-tune model parameters** (embedding_dim, num_layers)
3. **Implement feedback loop** (track conversions)
4. **Set up production monitoring** (alerts, dashboards)
5. **Scale horizontally** (add more ML Engine instances)
6. **Upgrade to advanced models** (Two-Tower, GNN when needed)

---

**Congratulations!** You've successfully built and deployed a production-ready recommendation system. 🎉

For more details, see:
- [Development Roadmap](docs/DEVELOPMENT_ROADMAP.md)
- [API Documentation](http://localhost:8000/docs)
- [System Architecture](docs/architecture/SYSTEM_OVERVIEW.md)
