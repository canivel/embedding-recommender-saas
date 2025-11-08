# Postman API Testing Setup

This guide explains how to import and use the Postman collection to test the Embedding Recommender SaaS APIs.

## Files Included

- `postman_collection.json` - Complete API collection with all endpoints
- `postman_environment.json` - Local environment variables

## Quick Start

### 1. Import Collection into Postman

#### Option A: Using Postman Desktop App
1. Open Postman
2. Click **Import** button (top left)
3. Click **Upload Files**
4. Select `postman_collection.json`
5. Click **Import**

#### Option B: Using File Path
1. Open Postman
2. Click **Import** button
3. Drag and drop `postman_collection.json` into the import window
4. Click **Import**

### 2. Import Environment

1. Click **Environments** in the left sidebar
2. Click **Import** button
3. Select `postman_environment.json`
4. Click **Import**
5. Select "Embedding Recommender - Local" from the environment dropdown (top right)

### 3. Test Your First API Call

#### Step 1: Login to Get Tokens
1. Expand **Backend API** → **Authentication** → **Login**
2. Click **Send**
3. Tokens will be automatically saved to collection variables (via Test script)
4. You should see:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "expires_in": 900,
     "user": {
       "id": "3340765d-a0ec-437f-9945-5c2550dc8dfb",
       "email": "admin@demo.com",
       "tenant_id": "1129bd7c-7601-46a6-b2c0-a6e09937397c",
       "role": "admin"
     }
   }
   ```

#### Step 2: Get ML Recommendations
1. Expand **ML Engine** → **Get Recommendations**
2. Click **Send**
3. You should see recommendations:
   ```json
   {
     "user_id": "user_001",
     "recommendations": [
       {
         "item_id": "item_0",
         "score": 0.9,
         "reason": "Based on your preferences"
       },
       ...
     ]
   }
   ```

## Collection Structure

```
Embedding Recommender SaaS API/
├── Backend API/
│   ├── Health & Status/
│   │   ├── Health Check
│   │   ├── Readiness Check
│   │   └── API Documentation
│   ├── Authentication/
│   │   ├── Login (auto-saves tokens)
│   │   └── Refresh Token (auto-updates access token)
│   ├── Recommendations/
│   │   └── Get Recommendations
│   └── Data Upload/
│       ├── Upload Interactions CSV
│       └── Upload Items CSV
├── ML Engine/
│   ├── Health Check
│   ├── Get Recommendations
│   ├── Trigger Model Training
│   └── Get Model Info
├── Data Pipeline/
│   ├── Health Check
│   ├── Upload Interactions
│   ├── Upload Items
│   └── Get Data Quality Metrics
└── Monitoring/
    ├── Prometheus Metrics
    └── Backend API Metrics
```

## Features

### Automatic Token Management

The collection includes **Test Scripts** that automatically:
- Save access tokens after login
- Save refresh tokens after login
- Update access tokens after refresh
- Set tenant_id and user_id from login response

**You don't need to manually copy/paste tokens!**

### Authentication Setup

Most endpoints use Bearer Token authentication. The collection is configured with:
```
Authorization: Bearer {{access_token}}
```

The `{{access_token}}` variable is automatically populated after login.

### Collection Variables

| Variable | Description | Auto-Updated |
|----------|-------------|--------------|
| `base_url` | Backend API URL (http://localhost:8000) | No |
| `ml_engine_url` | ML Engine URL (http://localhost:8001) | No |
| `data_pipeline_url` | Data Pipeline URL (http://localhost:8002) | No |
| `access_token` | JWT access token (15 min expiry) | Yes ✅ |
| `refresh_token` | JWT refresh token (7 day expiry) | Yes ✅ |
| `tenant_id` | Demo tenant ID | Yes ✅ |
| `user_id` | Demo user ID | Yes ✅ |

## Common Workflows

### Workflow 1: Test Authentication Flow

1. **Login** → Get tokens
2. **Get Recommendations** → Test authenticated endpoint
3. Wait 15+ minutes for token to expire
4. **Refresh Token** → Get new access token
5. **Get Recommendations** → Test with new token

### Workflow 2: Upload Data and Train Model

1. **Login** → Authenticate
2. **Data Pipeline** → **Upload Interactions** → Upload CSV file
3. **Data Pipeline** → **Upload Items** → Upload item catalog
4. **ML Engine** → **Trigger Model Training** → Start training
5. **ML Engine** → **Get Model Info** → Check training status
6. **ML Engine** → **Get Recommendations** → Test trained model

### Workflow 3: Monitor System Health

1. **Backend API** → **Health Check**
2. **ML Engine** → **Health Check**
3. **Data Pipeline** → **Health Check**
4. **Monitoring** → **Backend API Metrics** → View Prometheus metrics

## Test Data

### Sample Interaction CSV Format

Create a file `test_interactions.csv`:
```csv
user_id,item_id,interaction_type,timestamp,rating,duration_seconds
user_001,item_042,view,2024-01-15T10:30:00Z,,45
user_001,item_042,purchase,2024-01-15T10:35:00Z,5,
user_002,item_123,view,2024-01-15T11:00:00Z,,120
user_002,item_123,add_to_cart,2024-01-15T11:02:00Z,,
```

### Sample Items CSV Format

Create a file `test_items.csv`:
```csv
item_id,name,category,price,description
item_042,Wireless Headphones,Electronics,99.99,Premium noise-canceling headphones
item_123,Running Shoes,Sports,79.99,Lightweight athletic shoes
```

## Troubleshooting

### Error: "Authentication required"

**Solution**: Run the **Login** request first to get access tokens.

### Error: "Token expired"

**Solution**: Run the **Refresh Token** request to get a new access token.

### Error: "Field required: tenant_id"

**Solution**: Make sure you've run **Login** first. The tenant_id is auto-populated from login response.

### No data in response

**Solution**:
1. Check that Docker containers are running: `docker-compose ps`
2. Verify health endpoints return "healthy" status
3. Check if sample data was generated (see TEST_RESULTS.md)

### Cannot upload file

**Solution**:
1. Ensure the file is in CSV format
2. File size should be < 10MB for testing
3. Check CSV headers match expected format

## Environment Variables

You can view/edit collection variables:
1. Click on the collection name
2. Go to **Variables** tab
3. See **Current value** and **Initial value**

Variables marked with lock icon 🔒 are secret and won't be exported.

## Tips

1. **Use Console**: View **Postman Console** (bottom left) to see request/response details and test script logs

2. **Save Responses**: Click **Save Response** → **Save as example** to keep successful responses for reference

3. **Create Test Users**: After getting admin access, you can create additional users via the admin endpoints

4. **Bulk Testing**: Use Postman **Collection Runner** to run all requests in sequence

5. **Export Results**: After testing, export collection with examples for documentation

## API Documentation

For detailed API documentation, visit:
- **Backend API**: http://localhost:8000/docs (Swagger UI)
- **ML Engine**: http://localhost:8001/docs
- **Data Pipeline**: http://localhost:8002/docs

## Support

For issues or questions:
1. Check [TEST_RESULTS.md](TEST_RESULTS.md) for test examples
2. Review API documentation at `/docs` endpoints
3. Check Docker logs: `docker-compose logs <service-name>`

## Next Steps

After testing with Postman:
1. Integrate with frontend applications
2. Set up automated API tests
3. Configure production environment
4. Implement monitoring alerts

Happy Testing! 🚀
