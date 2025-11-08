# Quick Start Guide

Get the data pipeline running in 5 minutes!

## Prerequisites

- Python 3.11+
- UV package manager
- Docker and Docker Compose

## Step 1: Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Step 2: Install Dependencies

```bash
cd data-pipeline
uv sync
```

This will install all required packages using UV.

## Step 3: Start Infrastructure

```bash
# From project root
cd ..
docker-compose up -d kafka zookeeper minio
```

Wait ~30 seconds for services to be ready.

## Step 4: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit if needed (defaults work for local development)
```

## Step 5: Start the Service

```bash
# Development mode with hot reload
uv run uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

The service is now running at `http://localhost:8002`

## Step 6: Verify Health

```bash
curl http://localhost:8002/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "data-pipeline",
  "version": "0.1.0",
  "kafka_connected": true,
  "s3_connected": true
}
```

## Step 7: Generate Sample Data

```bash
# Generate 10K users, 5K items, 100K interactions
python generate_sample_data.py

# Or generate with custom parameters
python generate_sample_data.py --users 1000 --items 500 --interactions 5000
```

This creates:
- `sample_data/items.csv`
- `sample_data/interactions.csv`

## Step 8: Upload Sample Data

```bash
# Generate AND upload in one command
python generate_sample_data.py --upload

# Or upload existing files manually
curl -X POST 'http://localhost:8002/internal/data/upload-csv?tenant_id=demo&data_type=items' \
  -F 'file=@sample_data/items.csv'

curl -X POST 'http://localhost:8002/internal/data/upload-csv?tenant_id=demo&data_type=interactions' \
  -F 'file=@sample_data/interactions.csv'
```

## Step 9: Run Tests

```bash
# Test core functionality
python test_pipeline.py
```

## Step 10: Explore the API

Open your browser to:
- **API Docs**: http://localhost:8002/docs
- **Alternative Docs**: http://localhost:8002/redoc
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)

## Common Commands

### Run with Docker

```bash
# Build image
docker build -t data-pipeline:latest .

# Run container
docker-compose up data-pipeline
```

### Check Logs

```bash
# Service logs
docker-compose logs -f data-pipeline

# Kafka logs
docker-compose logs -f kafka

# MinIO logs
docker-compose logs -f minio
```

### Access MinIO

1. Open http://localhost:9001
2. Login: minioadmin / minioadmin
3. Browse buckets: raw-data, processed-data, features, training-data

### View Kafka Topics

```bash
# List topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# View messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions-raw \
  --from-beginning
```

## API Examples

### Upload CSV

```bash
curl -X POST 'http://localhost:8002/internal/data/upload-csv?tenant_id=demo&data_type=interactions' \
  -F 'file=@sample_data/interactions.csv'
```

### Upload JSON

```bash
curl -X POST 'http://localhost:8002/internal/data/interactions?tenant_id=demo' \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "user_id": "user_001",
      "item_id": "item_1234",
      "interaction_type": "purchase",
      "timestamp": "2025-01-01T10:00:00Z",
      "rating": 5.0
    }
  ]'
```

### Validate Data

```bash
curl -X POST 'http://localhost:8002/api/validation/validate' \
  -H 'Content-Type: application/json' \
  -d '{
    "data_type": "interactions",
    "sample_data": [
      {
        "user_id": "user_001",
        "item_id": "item_1234",
        "interaction_type": "purchase",
        "timestamp": "2025-01-01T10:00:00Z"
      }
    ]
  }'
```

### Get Schema

```bash
curl http://localhost:8002/api/validation/schema/interactions
curl http://localhost:8002/api/validation/schema/items
```

## Python Usage

### Generate Features

```python
from src.etl.feature_engineering import FeatureEngineer
import pandas as pd

# Load data
interactions = pd.read_csv("sample_data/interactions.csv")
items = pd.read_csv("sample_data/items.csv")

# Compute features
engineer = FeatureEngineer()
user_features = engineer.compute_user_features(interactions)
item_features = engineer.compute_item_features(interactions, items)

# Save to S3
engineer.save_features(user_features, item_features)
```

### Generate Training Data

```python
from src.etl.negative_sampling import NegativeSampler
import pandas as pd

# Load data
interactions = pd.read_csv("sample_data/interactions.csv")
items = pd.read_csv("sample_data/items.csv")

# Generate training data
sampler = NegativeSampler(negative_ratio=4)
training_data = sampler.generate_training_data(
    interactions,
    items,
    positive_interaction_types=['click', 'purchase', 'like']
)

# Save to S3
sampler.save_training_data(training_data)

# Split train/test
splits = sampler.split_train_test(training_data, test_size=0.2)
train = splits['train']
test = splits['test']
```

## Troubleshooting

### Port already in use

```bash
# Check what's using port 8002
lsof -i :8002

# Kill the process or use a different port
uvicorn src.main:app --port 8003
```

### Kafka not connecting

```bash
# Check if Kafka is running
docker-compose ps kafka

# Restart Kafka
docker-compose restart kafka

# Check logs
docker-compose logs kafka
```

### MinIO not connecting

```bash
# Check if MinIO is running
docker-compose ps minio

# Restart MinIO
docker-compose restart minio

# Test connection
curl http://localhost:9000/minio/health/live
```

### Dependencies not installing

```bash
# Clear UV cache
rm -rf .venv

# Reinstall
uv sync
```

## Next Steps

1. **Read the full README**: See `README.md` for detailed documentation
2. **Explore the code**: Check out the source code in `src/`
3. **Run the pipeline**: Process data with feature engineering and negative sampling
4. **Integrate with ML**: Use training data for model training
5. **Monitor**: Set up Prometheus and Grafana for monitoring

## Getting Help

- Check logs: `docker-compose logs -f data-pipeline`
- Run tests: `python test_pipeline.py`
- API documentation: http://localhost:8002/docs
- Health check: http://localhost:8002/health

Happy data pipelining!
