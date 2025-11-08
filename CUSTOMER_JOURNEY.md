# End-to-End Customer Journey Guide

This guide walks through the complete customer experience with the Embedding Recommender SaaS platform, from initial onboarding to getting personalized recommendations.

## Overview: The Customer Story

**Meet Sarah's E-commerce Store** 🛍️

Sarah runs an online electronics store with 10,000 products and 5,000 active customers. She wants to implement personalized product recommendations to increase sales. Here's her journey with our platform.

---

## Phase 1: Onboarding (Day 1)

### Step 1: Company Signs Up

**What Happens:**
- Sarah visits the platform and creates an account
- System creates a new **tenant** for "Sarah's Electronics"
- System generates isolated database, S3 storage, and API credentials

**API Call (Backend - Admin creates tenant):**
```http
POST http://localhost:8000/api/v1/admin/tenants
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Sarah's Electronics",
  "slug": "sarahs-electronics",
  "settings": {
    "recommendation_model": "lightgcn",
    "max_recommendations": 50,
    "enable_real_time": true
  }
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
  "name": "Sarah's Electronics",
  "slug": "sarahs-electronics",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**What Sarah Gets:**
- Tenant ID: `a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6`
- Admin account credentials
- API key for backend integration
- S3 buckets for her data

---

### Step 2: Sarah Creates Her Admin Account

**API Call:**
```http
POST http://localhost:8000/api/v1/admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "sarah@electronicsstore.com",
  "password": "SecurePass123!",
  "tenant_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
  "role": "admin"
}
```

**Response:**
```json
{
  "id": "user_sarah_001",
  "email": "sarah@electronicsstore.com",
  "tenant_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
  "role": "admin",
  "status": "active"
}
```

---

### Step 3: Sarah Generates API Key for Her Website

**What Happens:**
Sarah logs into the admin panel and generates an API key to integrate with her e-commerce website.

**API Call:**
```http
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "sarah@electronicsstore.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 900,
  "user": {
    "id": "user_sarah_001",
    "email": "sarah@electronicsstore.com",
    "tenant_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
    "role": "admin"
  }
}
```

**Then Create API Key:**
```http
POST http://localhost:8000/api/v1/api-keys
Authorization: Bearer <sarah_access_token>
Content-Type: application/json

{
  "name": "Production Website",
  "scopes": ["recommendations:read", "interactions:write"]
}
```

**Response:**
```json
{
  "id": "key_001",
  "name": "Production Website",
  "api_key": "sk_live_a1b2c3d4e5f6g7h8i9j0",
  "key_prefix": "sk_live_a1b",
  "scopes": ["recommendations:read", "interactions:write"],
  "created_at": "2024-01-15T10:05:00Z"
}
```

**⚠️ Important:** Sarah saves this API key securely - it's shown only once!

---

## Phase 2: Data Import (Day 1-2)

### Step 4: Upload Product Catalog

**What Happens:**
Sarah exports her product catalog from her e-commerce database and uploads it.

**Sample CSV File (`products.csv`):**
```csv
item_id,name,category,price,description,brand,tags
PROD_001,Wireless Headphones,Audio,99.99,Premium noise-canceling headphones,AudioTech,wireless|bluetooth|premium
PROD_002,Gaming Laptop,Computers,1299.99,High-performance gaming laptop,TechPro,gaming|laptop|rgb
PROD_003,Smart Watch,Wearables,249.99,Fitness tracking smartwatch,FitTech,fitness|smartwatch|health
PROD_004,USB-C Cable,Accessories,12.99,Fast charging USB-C cable,GenericBrand,cable|charging|usb
```

**API Call (Data Pipeline):**
```http
POST http://localhost:8002/api/v1/upload/items
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: multipart/form-data

file: products.csv
tenant_id: a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6
```

**Response:**
```json
{
  "status": "success",
  "rows_accepted": 10000,
  "rows_rejected": 15,
  "validation_errors": [
    {
      "row": 42,
      "error": "Invalid price format",
      "item_id": "PROD_042"
    }
  ],
  "storage_location": "s3://embeddings-item-data/a1b2c3d4/items_20240115.parquet"
}
```

**What Happens Behind the Scenes:**
1. CSV is validated (schema, data types, required fields)
2. Data quality checks run (completeness, uniqueness)
3. Valid rows converted to Parquet format
4. Stored in tenant's isolated S3 bucket
5. Metadata indexed in PostgreSQL
6. Kafka event published: `item-catalog-updated`

---

### Step 5: Upload Historical Interaction Data

**What Happens:**
Sarah exports 6 months of historical customer behavior data.

**Sample CSV File (`interactions.csv`):**
```csv
user_id,item_id,interaction_type,timestamp,rating,duration_seconds
USER_001,PROD_001,view,2024-01-10T14:23:00Z,,45
USER_001,PROD_001,add_to_cart,2024-01-10T14:25:00Z,,
USER_001,PROD_001,purchase,2024-01-10T14:30:00Z,5,
USER_002,PROD_003,view,2024-01-10T15:00:00Z,,120
USER_002,PROD_003,purchase,2024-01-10T15:05:00Z,5,
USER_003,PROD_002,view,2024-01-11T09:15:00Z,,300
USER_003,PROD_002,add_to_cart,2024-01-11T09:20:00Z,,
```

**API Call:**
```http
POST http://localhost:8002/api/v1/upload/interactions
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: multipart/form-data

file: interactions.csv
tenant_id: a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6
```

**Response:**
```json
{
  "status": "success",
  "rows_accepted": 150000,
  "rows_rejected": 234,
  "validation_errors": [
    {
      "row": 1523,
      "error": "Invalid timestamp format"
    }
  ],
  "storage_location": "s3://embeddings-training-data/a1b2c3d4/interactions_20240115.parquet",
  "statistics": {
    "unique_users": 4823,
    "unique_items": 8976,
    "interaction_types": {
      "view": 98000,
      "add_to_cart": 32000,
      "purchase": 20000
    }
  }
}
```

**What Happens Behind the Scenes:**
1. Interactions validated (user/item existence, timestamp format)
2. Duplicate detection and removal
3. Data quality scoring
4. Stored in Parquet format with partitioning by date
5. Kafka event: `interactions-uploaded`
6. Triggers automatic data quality report

---

## Phase 3: Model Training (Day 2)

### Step 6: Train Initial Recommendation Model

**What Happens:**
Sarah triggers the first model training using her historical data.

**API Call:**
```http
POST http://localhost:8001/api/v1/train
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "tenant_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
  "model_type": "lightgcn",
  "hyperparameters": {
    "embedding_dim": 64,
    "num_layers": 3,
    "learning_rate": 0.001,
    "batch_size": 2048,
    "epochs": 100,
    "negative_samples": 4
  }
}
```

**Response:**
```json
{
  "job_id": "training_job_001",
  "status": "started",
  "estimated_duration_minutes": 45,
  "progress_url": "/api/v1/training/training_job_001/progress"
}
```

**Sarah Monitors Training Progress:**
```http
GET http://localhost:8001/api/v1/training/training_job_001/progress
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
```

**Progress Response (polling every 30 seconds):**
```json
{
  "job_id": "training_job_001",
  "status": "training",
  "progress": 0.65,
  "current_epoch": 65,
  "total_epochs": 100,
  "metrics": {
    "train_loss": 0.234,
    "val_ndcg@10": 0.342,
    "val_recall@20": 0.456
  },
  "estimated_completion": "2024-01-15T11:30:00Z"
}
```

**Training Complete Response:**
```json
{
  "job_id": "training_job_001",
  "status": "completed",
  "progress": 1.0,
  "model_version": "v1.0_20240115",
  "final_metrics": {
    "ndcg@10": 0.378,
    "recall@20": 0.512,
    "precision@10": 0.234
  },
  "model_location": "s3://embeddings-models/a1b2c3d4/lightgcn_v1.0_20240115.pt",
  "deployment_status": "deployed",
  "training_duration_seconds": 2734
}
```

**What Happens Behind the Scenes:**
1. Data loaded from S3 (150K interactions, 10K items)
2. User-item interaction graph constructed
3. LightGCN model initialized with embeddings
4. Training with negative sampling
5. Validation every 10 epochs
6. Early stopping if no improvement
7. Best model saved to S3
8. FAISS index built for fast similarity search
9. Model deployed to serving layer
10. Kafka event: `model-deployed`

---

## Phase 4: Integration with Website (Day 3)

### Step 7: Sarah Integrates API into Her Website

**Frontend Code (Sarah's E-commerce Site):**

```javascript
// Sarah's website - product page
class RecommendationWidget {
  constructor(apiKey, tenantId) {
    this.apiKey = apiKey;
    this.tenantId = tenantId;
    this.baseUrl = 'https://api.embeddings-saas.com'; // Production URL
  }

  // Get recommendations for logged-in user
  async getRecommendations(userId, context = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1/recommendations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        count: 10,
        filters: context.filters,
        context: {
          page: context.page,
          device: context.device,
          current_item: context.currentItem
        }
      })
    });

    return await response.json();
  }

  // Track user interaction
  async trackInteraction(userId, itemId, interactionType) {
    await fetch(`${this.baseUrl}/api/v1/interactions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        item_id: itemId,
        interaction_type: interactionType,
        timestamp: new Date().toISOString()
      })
    });
  }

  // Render recommendations on page
  async renderRecommendations(containerId, userId) {
    const data = await this.getRecommendations(userId, {
      page: 'homepage',
      device: this.getDeviceType()
    });

    const container = document.getElementById(containerId);
    container.innerHTML = `
      <h3>Recommended For You</h3>
      <div class="recommendations-grid">
        ${data.recommendations.map(item => `
          <div class="product-card" data-item-id="${item.item_id}">
            <img src="${item.image_url}" alt="${item.name}">
            <h4>${item.name}</h4>
            <p class="price">$${item.price}</p>
            <span class="score">${Math.round(item.score * 100)}% match</span>
          </div>
        `).join('')}
      </div>
    `;

    // Track impressions
    this.trackInteraction(userId, null, 'recommendations_shown');
  }

  getDeviceType() {
    return window.innerWidth < 768 ? 'mobile' : 'desktop';
  }
}

// Initialize on Sarah's website
const recommender = new RecommendationWidget(
  'sk_live_a1b2c3d4e5f6g7h8i9j0',
  'a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6'
);

// Show recommendations when user logs in
document.addEventListener('userLoggedIn', (event) => {
  recommender.renderRecommendations('recommendations-container', event.detail.userId);
});

// Track product views
document.querySelectorAll('.product-link').forEach(link => {
  link.addEventListener('click', (e) => {
    const itemId = e.target.dataset.itemId;
    const userId = getCurrentUserId();
    recommender.trackInteraction(userId, itemId, 'view');
  });
});

// Track add to cart
document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const itemId = e.target.dataset.itemId;
    const userId = getCurrentUserId();
    recommender.trackInteraction(userId, itemId, 'add_to_cart');
  });
});
```

---

## Phase 5: Live Customer Interactions (Day 4+)

### Step 8: Real Customer Uses Sarah's Website

**Meet John - A Real Customer** 👨

John visits Sarah's electronics store looking for headphones.

#### 8a. John Browses Homepage

**What Happens:**
- Website calls API to get personalized recommendations
- System uses John's past behavior + collaborative filtering

**API Call:**
```http
POST http://localhost:8000/api/v1/recommendations
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "user_id": "USER_JOHN_001",
  "count": 10,
  "context": {
    "page": "homepage",
    "device": "mobile",
    "time_of_day": "evening"
  }
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "item_id": "PROD_001",
      "name": "Wireless Headphones",
      "category": "Audio",
      "price": 99.99,
      "score": 0.92,
      "image_url": "https://cdn.sarahs.com/prod_001.jpg",
      "reason": "Based on your recent audio purchases"
    },
    {
      "item_id": "PROD_015",
      "name": "Bluetooth Speaker",
      "category": "Audio",
      "price": 79.99,
      "score": 0.87,
      "reason": "Popular with customers like you"
    },
    {
      "item_id": "PROD_023",
      "name": "Noise Cancelling Earbuds",
      "category": "Audio",
      "price": 149.99,
      "score": 0.84,
      "reason": "Trending in Audio"
    }
  ],
  "metadata": {
    "model_version": "v1.0_20240115",
    "latency_ms": 23,
    "algorithm": "lightgcn + collaborative_filtering"
  }
}
```

**What Happens Behind the Scenes:**
1. API receives request with John's user_id
2. ML Engine checks Redis cache for John's embedding
3. Cache miss → loads user embedding from FAISS index
4. Performs approximate nearest neighbor search
5. Filters out items John already purchased
6. Applies context (mobile, evening) for reranking
7. Returns top 10 items with scores
8. Caches result for 5 minutes
9. Logs request to usage tracker
10. Updates Prometheus metrics

---

#### 8b. John Clicks on Wireless Headphones

**What Happens:**
Website tracks the interaction in real-time.

**API Call:**
```http
POST http://localhost:8000/api/v1/interactions
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "user_id": "USER_JOHN_001",
  "item_id": "PROD_001",
  "interaction_type": "view",
  "timestamp": "2024-01-16T19:23:45Z",
  "context": {
    "source": "homepage_recommendations",
    "device": "mobile"
  }
}
```

**Response:**
```json
{
  "status": "tracked",
  "interaction_id": "int_12345",
  "processed_at": "2024-01-16T19:23:45.123Z"
}
```

**What Happens Behind the Scenes:**
1. Interaction stored in Kafka topic `user-interactions`
2. Real-time stream processing updates user profile
3. Event logged to PostgreSQL
4. User embedding slightly adjusted (incremental learning)
5. Redis cache invalidated for this user
6. Analytics dashboard updated

---

#### 8c. John Views Product Page - Gets "Similar Items"

**What Happens:**
Product page shows "Customers who viewed this also viewed..."

**API Call:**
```http
POST http://localhost:8000/api/v1/recommendations/similar
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "item_id": "PROD_001",
  "count": 6,
  "tenant_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6"
}
```

**Response:**
```json
{
  "similar_items": [
    {
      "item_id": "PROD_023",
      "name": "Noise Cancelling Earbuds",
      "similarity_score": 0.94,
      "price": 149.99
    },
    {
      "item_id": "PROD_015",
      "name": "Bluetooth Speaker",
      "similarity_score": 0.89,
      "price": 79.99
    },
    {
      "item_id": "PROD_042",
      "name": "Wireless Headphones Pro",
      "similarity_score": 0.85,
      "price": 199.99
    }
  ]
}
```

**What Happens Behind the Scenes:**
1. Loads item embedding for PROD_001
2. Performs FAISS similarity search
3. Returns top-k most similar items
4. Filters by availability and price range
5. Ultra-fast (<10ms) response from cache

---

#### 8d. John Adds to Cart

**API Call:**
```http
POST http://localhost:8000/api/v1/interactions
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "user_id": "USER_JOHN_001",
  "item_id": "PROD_001",
  "interaction_type": "add_to_cart",
  "timestamp": "2024-01-16T19:25:30Z"
}
```

---

#### 8e. John Completes Purchase

**API Call:**
```http
POST http://localhost:8000/api/v1/interactions
Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "user_id": "USER_JOHN_001",
  "item_id": "PROD_001",
  "interaction_type": "purchase",
  "timestamp": "2024-01-16T19:30:00Z",
  "metadata": {
    "order_id": "ORD_98765",
    "price": 99.99,
    "quantity": 1
  }
}
```

**Response:**
```json
{
  "status": "tracked",
  "interaction_id": "int_12348",
  "processed_at": "2024-01-16T19:30:00.456Z",
  "next_actions": {
    "retrain_recommended": false,
    "incremental_update": true
  }
}
```

**What Happens Behind the Scenes:**
1. Purchase event sent to Kafka with high priority
2. John's user embedding updated with strong positive signal
3. Item popularity score increased
4. Collaborative filtering graph updated
5. Similar users get influenced by John's purchase
6. Email trigger sent (handled by Sarah's system)

---

## Phase 6: Ongoing Operations

### Step 9: Sarah Monitors Performance (Daily)

**Sarah's Admin Dashboard:**

```http
GET http://localhost:8000/api/v1/analytics/tenant/a1b2c3d4/dashboard
Authorization: Bearer <sarah_access_token>
```

**Response:**
```json
{
  "period": "last_7_days",
  "metrics": {
    "total_api_calls": 245000,
    "total_recommendations_served": 198000,
    "click_through_rate": 0.234,
    "conversion_rate": 0.045,
    "average_latency_ms": 28,
    "cache_hit_rate": 0.87,
    "model_performance": {
      "ndcg@10": 0.382,
      "recall@20": 0.521,
      "precision@10": 0.241
    },
    "revenue_impact": {
      "attributed_revenue": 45678.90,
      "attributed_orders": 523,
      "average_order_value": 87.32
    }
  },
  "top_recommended_items": [
    {"item_id": "PROD_001", "impressions": 12500, "clicks": 2890, "purchases": 234},
    {"item_id": "PROD_015", "impressions": 11200, "clicks": 2456, "purchases": 189}
  ],
  "data_quality": {
    "freshness_hours": 0.25,
    "completeness_percent": 98.7,
    "validity_percent": 99.2
  }
}
```

---

### Step 10: Automatic Model Retraining (Weekly)

**What Happens:**
System automatically triggers retraining when:
- 7 days have passed since last training
- 10,000+ new interactions collected
- Model performance drops below threshold

**Automatic API Call (Scheduled Job):**
```http
POST http://localhost:8001/api/v1/train
Authorization: Bearer <system_token>
Content-Type: application/json

{
  "tenant_id": "a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
  "model_type": "lightgcn",
  "training_mode": "incremental",
  "auto_deploy": true
}
```

**What Happens Behind the Scenes:**
1. New interactions since last training loaded
2. Existing model weights loaded as starting point
3. Incremental training (faster than full retrain)
4. A/B testing: 10% traffic to new model, 90% to old
5. If metrics improve → gradual rollout to 100%
6. Old model kept as backup for 30 days

---

## Complete Flow Summary

```
1. ONBOARDING (Day 1)
   └─ Sarah creates account
   └─ Gets tenant ID + API key
   └─ Sets up billing

2. DATA IMPORT (Day 1-2)
   └─ Uploads product catalog (10K items)
   └─ Uploads historical interactions (150K events)
   └─ Data validation + quality checks

3. MODEL TRAINING (Day 2)
   └─ Triggers first training
   └─ Waits 45 minutes
   └─ Model deployed automatically

4. INTEGRATION (Day 3)
   └─ Adds JS widget to website
   └─ Tests on staging environment
   └─ Deploys to production

5. LIVE USAGE (Day 4+)
   John (Customer) Journey:
   ├─ Visits homepage → sees personalized recs
   ├─ Clicks product → tracked
   ├─ Views product page → sees similar items
   ├─ Adds to cart → tracked
   └─ Purchases → tracked + model updated

6. CONTINUOUS IMPROVEMENT
   ├─ Daily: Sarah monitors dashboard
   ├─ Weekly: Automatic model retraining
   └─ Monthly: Performance review + optimization
```

---

## Key Benefits Sarah Experiences

### Week 1
- ✅ Personalized recommendations live on website
- ✅ 23% increase in product page views
- ✅ 12% increase in add-to-cart rate

### Week 4
- ✅ 45% increase in recommendation click-through rate
- ✅ 18% increase in conversion rate
- ✅ $45K additional revenue attributed to recommendations
- ✅ Average order value increased by 15%

### Month 3
- ✅ Model accuracy improved to 92% (from 78%)
- ✅ 500K+ recommendations served
- ✅ <30ms average API latency
- ✅ 99.9% uptime

---

## Technical Architecture Involved

```
Customer Browser (John)
    ↓
Sarah's Website (Frontend)
    ↓
API Gateway (Port 8000) ← API Key Authentication
    ↓
┌─────────────┬───────────────┬──────────────┐
│ Backend API │  ML Engine    │ Data Pipeline│
│ (FastAPI)   │  (PyTorch)    │ (Kafka)      │
└─────────────┴───────────────┴──────────────┘
    ↓               ↓                ↓
┌─────────────┬───────────────┬──────────────┐
│ PostgreSQL  │  Redis Cache  │  MinIO S3    │
│ (Metadata)  │  (Embeddings) │  (Models)    │
└─────────────┴───────────────┴──────────────┘
    ↓
Monitoring (Prometheus + Grafana)
```

---

## What Makes This System Special

1. **Multi-tenancy**: Sarah's data completely isolated from other customers
2. **Real-time**: Interactions processed in <100ms
3. **Scalable**: Handles millions of requests per day
4. **Intelligent**: ML model learns from every interaction
5. **Fast**: <30ms recommendation latency
6. **Accurate**: 92% prediction accuracy
7. **Automated**: Self-updating models
8. **Observable**: Complete monitoring and analytics

---

## Next Steps for Sarah

1. **A/B Testing**: Test different recommendation strategies
2. **Email Integration**: Send personalized product emails
3. **Mobile App**: Integrate recommendations into iOS/Android apps
4. **Advanced Features**:
   - Seasonal trend detection
   - Inventory-aware recommendations
   - Price optimization
   - Bundle recommendations

---

This is the complete journey from signup to success! 🚀
