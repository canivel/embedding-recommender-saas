# Data Pipeline Service

Data ingestion, validation, and ETL pipeline for the Embedding Recommender SaaS platform.

## Overview

This service handles:
- CSV upload and validation of interaction and item data
- Data quality checks using Great Expectations
- Feature engineering for users and items
- Negative sampling for training data generation
- Event streaming via Kafka
- Object storage in MinIO/S3

## Architecture

```
┌─────────────┐
│   CSV File  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  FastAPI Upload Endpoint    │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Data Validation            │
│  (Great Expectations)       │
└──────┬──────────────────────┘
       │
       ├────────────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│   MinIO/S3  │  │    Kafka    │
└─────────────┘  └─────────────┘
       │                │
       ▼                ▼
┌─────────────────────────────┐
│  Feature Engineering        │
│  Negative Sampling          │
└─────────────────────────────┘
```

## Features

### 1. Data Upload
- **CSV Upload**: Upload interaction and item data via CSV files
- **JSON API**: Upload data via REST API
- **Validation**: Automatic schema and quality validation
- **Storage**: Raw data stored in MinIO/S3 in Parquet format

### 2. Data Validation
- **Schema Validation**: Required columns, data types, value ranges
- **Quality Checks**: Null values, duplicates, valid enum values
- **Great Expectations**: Industry-standard data quality framework
- **Detailed Reports**: Validation errors and warnings

### 3. Feature Engineering
- **User Features**: Total interactions, unique items, ratings, recency
- **Item Features**: Popularity, engagement, purchase rate, ratings
- **Temporal Features**: Activity patterns, last interaction date
- **Storage**: Features saved to S3 in Parquet format

### 4. Negative Sampling
- **Training Data Generation**: Create positive and negative samples
- **Configurable Ratio**: Default 1:4 (positive:negative)
- **Smart Sampling**: Exclude items user has already interacted with
- **Zipf Distribution**: Realistic popularity patterns

### 5. Kafka Integration
- **Event Streaming**: Publish events for downstream processing
- **Topics**: `interactions-raw`, `items-catalog`, `features-processed`, `training-data`
- **Async Processing**: Background event processing

## Quick Start

### Prerequisites
- Python 3.11+
- UV package manager
- Docker (for infrastructure)

### Installation

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies**:
```bash
cd data-pipeline
uv sync
```

3. **Start infrastructure** (Kafka, MinIO):
```bash
# From project root
docker-compose up -d kafka zookeeper minio
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the service**:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

The service will be available at `http://localhost:8002`

### Docker Deployment

```bash
# Build image
docker build -t data-pipeline:latest .

# Run container
docker run -p 8002:8002 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 \
  -e S3_ENDPOINT=http://minio:9000 \
  data-pipeline:latest
```

Or use docker-compose:
```bash
docker-compose up data-pipeline
```

## API Documentation

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "data-pipeline",
  "version": "0.1.0",
  "timestamp": "2025-01-01T10:00:00Z",
  "kafka_connected": true,
  "s3_connected": true
}
```

### Upload CSV

```bash
POST /internal/data/upload-csv
```

Parameters:
- `tenant_id` (query): Tenant identifier
- `data_type` (query): "interactions" or "items"
- `file` (multipart): CSV file

Example:
```bash
curl -X POST "http://localhost:8002/internal/data/upload-csv?tenant_id=tenant_001&data_type=interactions" \
  -F "file=@interactions.csv"
```

Response:
```json
{
  "status": "success",
  "rows_accepted": 100000,
  "rows_rejected": 0,
  "s3_path": "s3://embeddings-data/tenant_001/raw/interactions/2025-01-01/20250101_100000.parquet",
  "validation_errors": []
}
```

### Upload Interactions (JSON)

```bash
POST /internal/data/interactions?tenant_id=tenant_001
```

Body:
```json
[
  {
    "user_id": "user_001",
    "item_id": "item_1234",
    "interaction_type": "purchase",
    "timestamp": "2025-01-01T10:00:00Z",
    "rating": 5.0
  }
]
```

### Upload Items (JSON)

```bash
POST /internal/data/items?tenant_id=tenant_001
```

Body:
```json
[
  {
    "item_id": "item_1234",
    "title": "Wireless Headphones",
    "category": "Electronics",
    "price": 99.99,
    "brand": "Sony"
  }
]
```

### Validate Data

```bash
POST /api/validation/validate
```

Body:
```json
{
  "data_type": "interactions",
  "sample_data": [
    {
      "user_id": "user_001",
      "item_id": "item_1234",
      "interaction_type": "purchase",
      "timestamp": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### Get Schema

```bash
GET /api/validation/schema/interactions
GET /api/validation/schema/items
```

## Data Schemas

### Interactions CSV

**Required columns:**
- `user_id` (string): Unique user identifier
- `item_id` (string): Unique item identifier
- `interaction_type` (string): Type of interaction
- `timestamp` (datetime): ISO 8601 format

**Optional columns:**
- `rating` (float): User rating (1.0-5.0)

**Valid interaction types:**
- `view`: User viewed the item
- `click`: User clicked on the item
- `purchase`: User purchased the item
- `like`: User liked the item
- `add_to_cart`: User added item to cart

**Example:**
```csv
user_id,item_id,interaction_type,timestamp,rating
user_001,item_1234,purchase,2025-01-01T10:00:00Z,5.0
user_002,item_5678,view,2025-01-01T10:05:00Z,
user_001,item_1234,like,2025-01-01T10:10:00Z,
```

### Items CSV

**Required columns:**
- `item_id` (string): Unique item identifier
- `title` (string): Item title/name

**Optional columns:**
- `category` (string): Item category
- `price` (float): Item price
- `brand` (string): Brand name
- `description` (string): Item description

**Example:**
```csv
item_id,title,category,price,brand
item_1234,Wireless Headphones,Electronics,99.99,Sony
item_5678,Smart Watch,Wearables,299.99,Apple
item_9012,Laptop,Computers,1299.99,Dell
```

## Sample Data Generation

Generate realistic sample data for testing:

```bash
# Using the data generator
python -m src.data_generator \
  --users 10000 \
  --items 5000 \
  --interactions 100000 \
  --output ./sample_data
```

This generates:
- **10,000 users** with varying activity levels
- **5,000 products** across 12 e-commerce categories
- **100,000 interactions** with realistic Zipf distribution (80/20 rule)
- Timestamps spanning last 90 days

Output files:
- `sample_data/items.csv`
- `sample_data/interactions.csv`

### Upload Sample Data

```bash
# Upload items
curl -X POST "http://localhost:8002/internal/data/upload-csv?tenant_id=demo&data_type=items" \
  -F "file=@sample_data/items.csv"

# Upload interactions
curl -X POST "http://localhost:8002/internal/data/upload-csv?tenant_id=demo&data_type=interactions" \
  -F "file=@sample_data/interactions.csv"
```

## ETL Pipeline

### Feature Engineering

```python
from src.etl.feature_engineering import FeatureEngineer
from src.storage.s3_client import s3_client
import pandas as pd

# Load data
interactions_df = pd.read_csv("interactions.csv")
items_df = pd.read_csv("items.csv")

# Initialize feature engineer
engineer = FeatureEngineer()

# Compute features
user_features = engineer.compute_user_features(interactions_df)
item_features = engineer.compute_item_features(interactions_df, items_df)

# Save to S3
engineer.save_features(user_features, item_features)
```

**User Features:**
- `total_interactions`: Total number of interactions
- `unique_items`: Number of unique items interacted with
- `avg_rating`: Average rating given
- `last_interaction`: Timestamp of last interaction
- `days_active`: Number of days user has been active
- `interactions_per_day`: Average interactions per day
- `num_views`, `num_clicks`, `num_purchases`, etc.
- `conversion_rate`: Purchase rate
- `recent_items`: List of recently interacted items (max 50)

**Item Features:**
- `total_interactions`: Total interaction count
- `unique_users`: Number of unique users
- `avg_rating`: Average rating
- `popularity_score`: Popularity metric
- `engagement_score`: Engagement metric
- `purchase_rate`: Conversion rate
- `click_through_rate`: CTR metric

### Negative Sampling

```python
from src.etl.negative_sampling import NegativeSampler
import pandas as pd

# Load data
interactions_df = pd.read_csv("interactions.csv")
items_df = pd.read_csv("items.csv")

# Initialize sampler
sampler = NegativeSampler(negative_ratio=4)

# Generate training data
training_data = sampler.generate_training_data(
    interactions_df,
    items_df,
    positive_interaction_types=['click', 'purchase', 'like']
)

# Save to S3
sampler.save_training_data(training_data)
```

**Training Data Format:**
```csv
user_id,item_id,label
user_001,item_1234,1.0
user_001,item_5678,0.0
user_001,item_9012,0.0
user_001,item_3456,0.0
user_001,item_7890,0.0
```

Where:
- `label = 1.0`: Positive sample (user interacted)
- `label = 0.0`: Negative sample (user did not interact)

**With Features:**
```python
# Generate training data with features
training_data = sampler.generate_training_data_with_features(
    interactions_df,
    user_features,
    item_features,
    items_df
)
```

## Configuration

Configuration is loaded from environment variables. See `.env.example`:

```bash
# Service
SERVICE_NAME=data-pipeline
VERSION=0.1.0
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://embeddings:embeddings_pass@localhost:5432/embeddings_saas

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_INTERACTIONS=interactions-raw
KAFKA_TOPIC_ITEMS=items-catalog
KAFKA_TOPIC_FEATURES=features-processed
KAFKA_TOPIC_TRAINING=training-data

# MinIO/S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_RAW=raw-data
S3_BUCKET_PROCESSED=processed-data
S3_BUCKET_TRAINING=training-data
S3_BUCKET_FEATURES=features

# Processing
NEGATIVE_SAMPLING_RATIO=4
MAX_INTERACTIONS_PER_USER=50
MIN_INTERACTIONS_PER_USER=5
MIN_INTERACTIONS_PER_ITEM=5
```

## Development

### Run Tests
```bash
uv run pytest
```

### Format Code
```bash
uv run black src/
```

### Lint Code
```bash
uv run ruff check src/
```

### Type Checking
```bash
uv run mypy src/
```

## Monitoring

### Metrics
- Prometheus metrics available at `/metrics`
- Track upload counts, validation failures, processing time

### Logging
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Logs sent to stdout (captured by Docker/K8s)

### Health Checks
- Liveness: `/health`
- Checks Kafka and S3 connectivity

## Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Test connection
kafkacat -b localhost:9092 -L
```

### MinIO Connection Issues
```bash
# Check MinIO is running
docker-compose ps minio

# Access MinIO console
open http://localhost:9001

# Check buckets
aws --endpoint-url http://localhost:9000 s3 ls
```

### Validation Failures
- Check data format matches schema
- Use `/api/validation/schema/{data_type}` to get expected format
- Use `/api/validation/validate` to test sample data
- Review validation error messages

## Performance

### Upload Performance
- CSV parsing: ~10K rows/sec
- Validation: ~5K rows/sec
- S3 upload: ~50MB/sec
- Recommended batch size: 10K-100K rows

### Feature Engineering
- Processing: ~100K interactions/sec
- Memory: ~2GB for 1M interactions
- Use PySpark for >10M interactions

### Negative Sampling
- Sampling rate: ~50K samples/sec
- Memory: ~1GB for 100K users, 50K items
- Ratio 1:4 generates 5x original data

## License

Copyright (c) 2025 Embedding Recommender SaaS

## Support

For issues and questions:
- GitHub Issues: [link]
- Documentation: [link]
- Email: support@example.com
