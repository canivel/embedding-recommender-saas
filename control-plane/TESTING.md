# Testing Airflow DAGs Locally

This guide provides instructions for testing the Airflow DAGs locally before deployment.

## Prerequisites

1. All services running via `bash scripts/start-local.sh`
2. Airflow UI accessible at http://localhost:8080
3. MinIO buckets initialized
4. Kafka topics created

## Test Scenarios

### Scenario 1: Test Tenant Model Training DAG

#### Setup Test Data

1. **Upload test training data to MinIO**:
```bash
# Using MinIO client
mc cp test-data.json minio/embeddings-training-data/training-data/test-tenant/latest/

# Or using Python with boto3
python scripts/upload-test-data.py
```

2. **Verify data exists**:
```bash
mc ls minio/embeddings-training-data/training-data/test-tenant/latest/
```

#### Run the DAG

1. Open Airflow UI: http://localhost:8080
2. Navigate to `tenant_model_training` DAG
3. Enable the DAG (toggle switch)
4. Click "Trigger DAG" (play button)
5. Add configuration:
```json
{
  "tenant_id": "test-tenant"
}
```
6. Click "Trigger"

#### Monitor Execution

1. **View Graph**: Click on the running DAG instance -> Graph tab
2. **Check Task Logs**: Click on individual tasks -> Log button
3. **Inspect XCom Data**: Click on task -> XCom tab

#### Expected Behavior

- **validate_training_data**: Should pass and find test files
- **trigger_ml_training**: Will fail if ML Engine not running (expected)
- **Subsequent tasks**: Will not run if previous tasks fail

#### Verify Results

Check task logs for:
```
Validation successful: {
  "tenant_id": "test-tenant",
  "file_count": X,
  "total_size_mb": Y
}
```

### Scenario 2: Test Data Quality Check DAG

#### Setup Test Database

1. **Insert test data into PostgreSQL**:
```sql
-- Connect to PostgreSQL
psql -h localhost -U postgres -d embeddings_saas

-- Insert test interactions
INSERT INTO user_interactions (user_id, item_id, interaction_type, timestamp, tenant_id)
VALUES
  ('user1', 'item1', 'view', NOW(), 'test-tenant'),
  ('user1', 'item2', 'click', NOW(), 'test-tenant'),
  ('user2', 'item1', 'purchase', NOW(), 'test-tenant');

-- Insert test items
INSERT INTO items (item_id, tenant_id, content, metadata, created_at)
VALUES
  ('item1', 'test-tenant', 'Test item 1', '{}', NOW()),
  ('item2', 'test-tenant', 'Test item 2', '{}', NOW());

-- Insert test users
INSERT INTO users (user_id, tenant_id, created_at)
VALUES
  ('user1', 'test-tenant', NOW()),
  ('user2', 'test-tenant', NOW());
```

#### Run the DAG

1. Open Airflow UI: http://localhost:8080
2. Navigate to `data_quality_check` DAG
3. Enable the DAG
4. Click "Trigger DAG"
5. Monitor execution

#### Expected Behavior

All quality checks should pass with test data:
- **check_data_completeness**: No NULL values
- **check_data_freshness**: Data is fresh (just inserted)
- **check_for_anomalies**: No anomalies detected
- **decide_alert_needed**: Should branch to `skip_alert`

#### Verify Results

Check logs for:
```
Completeness check results: {...}
Freshness check results: {...}
Anomaly check results: {...}
No critical issues detected
```

### Scenario 3: Test Alert Flow

#### Inject Bad Data

1. **Insert stale data**:
```sql
INSERT INTO user_interactions (user_id, item_id, interaction_type, timestamp, tenant_id)
VALUES ('user3', 'item3', 'view', NOW() - INTERVAL '48 hours', 'test-tenant');
```

2. **Insert data with NULL values**:
```sql
INSERT INTO user_interactions (user_id, item_id, interaction_type, timestamp, tenant_id)
VALUES (NULL, 'item4', 'view', NOW(), 'test-tenant');
```

#### Run the DAG

Trigger `data_quality_check` again

#### Expected Behavior

- Quality checks should detect issues
- **decide_alert_needed**: Should branch to `send_alert`
- **send_alert**: Will attempt to send alert (may fail if monitoring service not running)

#### Verify Alert

Check logs for:
```
Critical issues detected: [...]
Sending alert: {...}
```

## Testing via CLI

### Test DAG Import

```bash
# List all DAGs (verify no import errors)
docker-compose exec airflow-webserver airflow dags list

# Check for import errors
docker-compose exec airflow-webserver airflow dags list-import-errors
```

### Test Individual Tasks

```bash
# Test validate_training_data task
docker-compose exec airflow-webserver airflow tasks test \
  tenant_model_training validate_training_data 2025-01-01

# Test check_data_completeness task
docker-compose exec airflow-webserver airflow tasks test \
  data_quality_check check_data_completeness 2025-01-01
```

### Test Full DAG Run

```bash
# Test entire DAG without affecting metadata
docker-compose exec airflow-webserver airflow dags test \
  tenant_model_training 2025-01-01

docker-compose exec airflow-webserver airflow dags test \
  data_quality_check 2025-01-01
```

## Debugging Tips

### DAG Not Appearing

1. **Check file syntax**:
```bash
python -m py_compile control-plane/airflow/dags/tenant_model_training.py
```

2. **Check Airflow scheduler logs**:
```bash
docker-compose logs -f airflow-scheduler
```

3. **Verify DAG file is mounted**:
```bash
docker-compose exec airflow-webserver ls /opt/airflow/dags/
```

### Task Failing

1. **Check task logs** in Airflow UI
2. **Check service availability**:
```bash
# Test ML Engine
curl http://localhost:8000/health

# Test MinIO
curl http://localhost:9000/minio/health/live
```

3. **Check database connection**:
```bash
docker-compose exec postgres psql -U postgres -d embeddings_saas -c "SELECT 1;"
```

### Connection Errors

If tasks fail with connection errors:

1. **Add Airflow connections**:

Go to Admin -> Connections in Airflow UI

**MinIO Connection**:
- Conn Id: `minio_default`
- Conn Type: `Amazon Web Services`
- Extra:
```json
{
  "aws_access_key_id": "minioadmin",
  "aws_secret_access_key": "minioadmin",
  "endpoint_url": "http://minio:9000"
}
```

**PostgreSQL Connection**:
- Conn Id: `postgres_default`
- Conn Type: `Postgres`
- Host: `postgres`
- Schema: `embeddings_saas`
- Login: `postgres`
- Password: `postgres`
- Port: `5432`

## Mock Services for Testing

If ML Engine or other services are not running, you can mock them:

### Mock ML Engine

Create a simple Flask app:

```python
# mock-ml-engine.py
from flask import Flask, jsonify, request
import uuid

app = Flask(__name__)
jobs = {}

@app.route('/api/v1/train', methods=['POST'])
def train():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'completed', 'model_path': 's3://models/test/'}
    return jsonify({'job_id': job_id})

@app.route('/api/v1/jobs/<job_id>/status', methods=['GET'])
def status(job_id):
    return jsonify(jobs.get(job_id, {'status': 'completed'}))

@app.route('/api/v1/index/build', methods=['POST'])
def build_index():
    return jsonify({'index_path': 's3://indices/test/'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

Run it:
```bash
python mock-ml-engine.py
```

## Performance Testing

### Test DAG Performance

1. **Enable task timing**:
Check task duration in Airflow UI -> Task Instance Details

2. **Monitor resource usage**:
```bash
docker stats
```

3. **Check database performance**:
```sql
SELECT * FROM pg_stat_activity WHERE datname = 'embeddings_saas';
```

### Load Testing

Trigger multiple DAG runs:
```bash
for i in {1..10}; do
  docker-compose exec airflow-webserver airflow dags trigger tenant_model_training \
    -c "{\"tenant_id\": \"tenant-$i\"}"
done
```

Monitor:
- Task queue length
- Resource consumption
- Task success/failure rates

## Cleanup

After testing:

```bash
# Clear DAG runs
docker-compose exec airflow-webserver airflow dags delete tenant_model_training
docker-compose exec airflow-webserver airflow dags delete data_quality_check

# Or clear all task instances
docker-compose exec airflow-webserver airflow db clean --clean-before-timestamp "2025-12-31"

# Remove test data
mc rm --recursive minio/embeddings-training-data/training-data/test-tenant/

# Clear PostgreSQL test data
psql -h localhost -U postgres -d embeddings_saas -c "DELETE FROM user_interactions WHERE tenant_id = 'test-tenant';"
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Run DAG validation
python -m pytest tests/test_dags.py

# Check DAG structure
airflow dags show tenant_model_training

# Run static analysis
pylint control-plane/airflow/dags/

# Check for security issues
bandit -r control-plane/airflow/dags/
```

## Next Steps

After successful local testing:
1. Deploy to staging environment
2. Run integration tests with real services
3. Monitor for 24 hours
4. Deploy to production
5. Set up alerting and monitoring
