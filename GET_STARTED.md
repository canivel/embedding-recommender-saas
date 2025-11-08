# Get Started as a New Customer 🚀

## Your Customer Journey Starts Here!

The platform is now fully running. Follow these steps to experience the complete customer journey from signup to getting recommendations.

---

## Step 1: Open the Customer Dashboard

**Open your browser and go to:**
```
http://localhost:3000
```

You'll see the **Customer Dashboard Homepage**. This is where new customers start.

---

## Step 2: Create Your Account (Sign Up)

Since you're a new customer, you need to create an account.

### Option A: Use the Signup Page

1. Click on **"Sign Up"** or navigate to:
   ```
   http://localhost:3000/signup
   ```

2. Fill in the signup form with your company details:
   - **Company Name**: Your E-commerce Store Name (e.g., "My Electronics Store")
   - **Email**: Your email address
   - **Password**: Choose a secure password (minimum 8 characters)

3. Click **"Create Account"**

**What happens behind the scenes:**
- A new tenant is created in the database
- Your company gets isolated storage buckets in MinIO
- An admin user account is created for you
- You're automatically logged in

### Option B: Use the Demo Account (Quick Start)

If you want to skip signup and jump right in, use the existing demo account:

**Go to Login:**
```
http://localhost:3000/login
```

**Demo Credentials:**
- **Email**: `admin@demo.com`
- **Password**: `demo123456`

---

## Step 3: Explore Your Dashboard

After logging in, you'll land on the main dashboard at:
```
http://localhost:3000/dashboard
```

Here you'll see:
- **API Usage Metrics**: Requests, latency, errors
- **Recommendation Stats**: Click-through rate, conversion rate
- **Revenue Impact**: How recommendations are driving sales
- **Quick Actions**: Upload data, generate API keys, view docs

---

## Step 4: Generate Your API Key

To integrate recommendations into your website, you need an API key.

1. **Go to API Keys page:**
   ```
   http://localhost:3000/api-keys
   ```

2. Click **"Generate New API Key"**

3. Fill in the details:
   - **Name**: "Production Website" or "Development"
   - **Scopes**: Select what this key can access:
     - ✅ `recommendations:read` - Get recommendations
     - ✅ `interactions:write` - Track user interactions
     - ✅ `data:upload` - Upload catalog/interaction data

4. Click **"Generate"**

5. **⚠️ IMPORTANT**: Copy and save the API key immediately - it's shown only once!
   ```
   sk_live_a1b2c3d4e5f6g7h8i9j0
   ```

---

## Step 5: Upload Your Product Catalog

Now let's upload some products so the system has data to work with.

### Option A: Use the UI

1. **Go to Data Upload page:**
   ```
   http://localhost:3000/data
   ```

2. Click **"Upload Items"** tab

3. **Prepare your CSV file** with this format:
   ```csv
   item_id,name,category,price,description,brand,tags
   PROD_001,Wireless Headphones,Audio,99.99,Premium noise-canceling,AudioTech,wireless|bluetooth
   PROD_002,Gaming Laptop,Computers,1299.99,High-performance gaming,TechPro,gaming|laptop
   PROD_003,Smart Watch,Wearables,249.99,Fitness tracking,FitTech,fitness|health
   ```

4. **Upload the file**

5. System validates and shows results:
   - Rows accepted
   - Rows rejected (if any)
   - Validation errors
   - Storage location in S3

### Option B: Use Sample Data (Quick Start)

We already generated sample data for you! It's in MinIO storage:
- **500 items** in electronics category
- **10,000 interactions** from customers

You can view this in MinIO console:
```
http://localhost:9001
Username: minioadmin
Password: minioadmin
```

Navigate to bucket: `embeddings-data`

---

## Step 6: Upload Interaction History (Optional)

If you have historical customer behavior data:

1. Go to **Data Upload page** → **"Upload Interactions"** tab

2. **Prepare CSV** with this format:
   ```csv
   user_id,item_id,interaction_type,timestamp,rating,duration_seconds
   USER_001,PROD_001,view,2024-01-15T10:30:00Z,,45
   USER_001,PROD_001,purchase,2024-01-15T10:35:00Z,5,
   USER_002,PROD_003,view,2024-01-15T11:00:00Z,,120
   ```

3. Upload and system will validate

**Interaction types supported:**
- `view` - User viewed product
- `add_to_cart` - User added to shopping cart
- `purchase` - User completed purchase
- `favorite` - User favorited/liked product

---

## Step 7: Train Your First Recommendation Model

Now that you have data, let's train a model!

### Using Postman (Easiest)

1. Open Postman
2. Import the collection from `postman_collection.json`
3. Run **"Login"** to get your token
4. Go to **ML Engine** → **"Trigger Model Training"**
5. Click **"Send"**

**Request body:**
```json
{
  "tenant_id": "YOUR_TENANT_ID",
  "model_type": "lightgcn",
  "hyperparameters": {
    "embedding_dim": 64,
    "num_layers": 3,
    "learning_rate": 0.001,
    "batch_size": 1024,
    "epochs": 100
  }
}
```

### Monitor Training Progress

The API returns a `job_id`. Use it to monitor:

**Check progress:**
```http
GET http://localhost:8001/api/v1/training/{job_id}/progress
```

**Training takes about 15-45 minutes** depending on data size.

You'll see:
- Current epoch
- Training loss
- Validation metrics (NDCG@10, Recall@20)
- Estimated completion time

When done, model is automatically deployed!

---

## Step 8: Test Recommendations

Once the model is trained, test it!

### Option A: Using the Dashboard

1. Go to **Test page:**
   ```
   http://localhost:3000/test
   ```

2. Enter a test user ID (e.g., `user_001`)

3. Click **"Get Recommendations"**

4. See personalized product recommendations with scores!

### Option B: Using Postman

1. Go to **ML Engine** → **"Get Recommendations"**

2. Request body:
   ```json
   {
     "tenant_id": "YOUR_TENANT_ID",
     "user_id": "user_001",
     "count": 10
   }
   ```

3. Response:
   ```json
   {
     "user_id": "user_001",
     "recommendations": [
       {
         "item_id": "item_0",
         "score": 0.92,
         "reason": "Based on your preferences"
       }
     ]
   }
   ```

---

## Step 9: Integrate into Your Website

Now integrate recommendations into your actual e-commerce website!

### JavaScript Integration Code

```javascript
// Initialize the recommendation widget
const recommender = new RecommendationWidget(
  'YOUR_API_KEY',  // From Step 4
  'YOUR_TENANT_ID'
);

// Get recommendations for a user
async function showRecommendations(userId) {
  const recs = await recommender.getRecommendations(userId, {
    count: 10,
    filters: { category: 'electronics' }
  });

  // Display recommendations on your page
  displayProducts(recs.recommendations);
}

// Track when user views a product
function trackProductView(userId, itemId) {
  recommender.trackInteraction(userId, itemId, 'view');
}

// Track when user makes a purchase
function trackPurchase(userId, itemId) {
  recommender.trackInteraction(userId, itemId, 'purchase');
}
```

See [CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md) for complete integration code!

---

## Step 10: Monitor Performance

Track how well recommendations are performing:

### Analytics Dashboard

Go to:
```
http://localhost:3000/analytics
```

You'll see:
- **API Metrics**: Total requests, latency, errors
- **Business Metrics**: Click-through rate, conversion rate
- **Revenue Impact**: Attributed sales from recommendations
- **Top Products**: Most recommended items
- **User Engagement**: Active users, interactions

### Prometheus Metrics

For technical metrics:
```
http://localhost:9090
```

Query examples:
- `up` - Service health
- `http_requests_total` - Total API requests
- `recommendation_latency_seconds` - API latency
- `model_accuracy` - Model performance

### Grafana Dashboards

For beautiful visualizations:
```
http://localhost:3001
```

Login: `admin` / `admin`

---

## Complete Customer Flow Summary

```
1. SIGNUP (You)
   └─ Create account at localhost:3000/signup
   └─ Or login with demo: admin@demo.com

2. GET API KEY
   └─ Go to localhost:3000/api-keys
   └─ Generate key for your website

3. UPLOAD DATA
   └─ Upload product catalog (CSV)
   └─ Upload interaction history (CSV)
   └─ Or use sample data already in MinIO

4. TRAIN MODEL
   └─ Use Postman: ML Engine → Trigger Training
   └─ Wait 15-45 minutes
   └─ Model auto-deploys when ready

5. TEST RECOMMENDATIONS
   └─ Use dashboard test page
   └─ Or use Postman to call API
   └─ See personalized recommendations!

6. INTEGRATE WEBSITE
   └─ Add JavaScript widget
   └─ Call API with your key
   └─ Show recommendations to customers

7. GO LIVE!
   └─ Real customers see recommendations
   └─ Track interactions automatically
   └─ Model updates weekly

8. MONITOR & OPTIMIZE
   └─ View analytics dashboard
   └─ Track revenue impact
   └─ Improve over time
```

---

## What's Currently Running

All services are ready for you:

### Frontend (You Start Here!)
- **Customer Dashboard**: http://localhost:3000
- **Admin Panel**: http://localhost:3002 (for platform admins)

### Backend APIs
- **Backend API**: http://localhost:8000
- **ML Engine**: http://localhost:8001
- **Data Pipeline**: http://localhost:8002

### Infrastructure
- **PostgreSQL**: localhost:5432 (your data)
- **Redis**: localhost:6379 (fast cache)
- **MinIO**: http://localhost:9001 (file storage)
- **Kafka**: localhost:9092 (event streaming)

### Monitoring
- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3001 (dashboards)
- **Jaeger**: http://localhost:16686 (tracing)

---

## Quick Actions to Try Now

### 1. Test the Demo Account (2 minutes)
```
1. Open http://localhost:3000/login
2. Login: admin@demo.com / demo123456
3. Explore the dashboard
```

### 2. Get Recommendations via API (1 minute)
```
1. Open Postman
2. Run "Login" request
3. Run "ML Engine → Get Recommendations"
4. See results!
```

### 3. View Sample Data (1 minute)
```
1. Open http://localhost:9001
2. Login: minioadmin / minioadmin
3. Browse bucket: embeddings-data
4. See 500 items and 10,000 interactions
```

### 4. Monitor System Health (1 minute)
```
1. Open http://localhost:9090
2. Click "Status" → "Targets"
3. See all services are UP
```

---

## Need Help?

- **Test Results**: See [TEST_RESULTS.md](TEST_RESULTS.md) for API examples
- **Customer Journey**: See [CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md) for detailed flow
- **Postman Setup**: See [POSTMAN_SETUP.md](POSTMAN_SETUP.md) for API testing
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

## Your Next Step

**👉 Open your browser now and go to:**
```
http://localhost:3000
```

Start your journey as a new customer! 🚀

You can either:
- **Sign up** for a new account (create your own company)
- **Login** with demo credentials to explore immediately

The choice is yours - enjoy exploring your new recommendation platform!
