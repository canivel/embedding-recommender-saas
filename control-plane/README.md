# Control Plane - Orchestration Layer

The Control Plane orchestrates all workflows for the Embedding Recommender SaaS platform using Apache Airflow.

## Overview

The control plane manages:
- **Model Training Pipelines**: Automated training of tenant-specific embedding models
- **Data Quality Monitoring**: Continuous validation of data completeness, freshness, and anomalies
- **Workflow Orchestration**: Scheduling and dependency management for all ML operations
- **Error Handling & Retries**: Robust error recovery for production reliability

## Architecture

```
control-plane/
├── airflow/
│   ├── dags/                    # Airflow DAG definitions
│   │   ├── tenant_model_training.py
│   │   └── data_quality_check.py
│   ├── plugins/                 # Custom Airflow plugins
│   ├── logs/                    # Airflow logs
│   ├── config/                  # Configuration files
│   ├── Dockerfile              # Airflow container image
│   └── requirements.txt        # Python dependencies
└── README.md                    # This file
```

## DAGs

### 1. Tenant Model Training (`tenant_model_training`)

**Schedule**: Daily at 2 AM (can be triggered manually)

**Purpose**: Orchestrates end-to-end ML model training and deployment for tenants

**Tasks**:
1. **validate_training_data**: Verify training data exists in S3/MinIO
   - Checks bucket existence
   - Counts data files
   - Validates data size

2. **trigger_ml_training**: Trigger ML Engine via HTTP API
   - Sends training configuration
   - Returns job ID for tracking

3. **wait_for_training_completion**: Poll for training completion
   - Max wait: 6 hours
   - Poll interval: 1 minute
   - Handles success/failure states

4. **build_faiss_index**: Build FAISS index for similarity search
   - Uses IVF (Inverted File) indexing
   - Optimized for fast retrieval

5. **deploy_to_production**: Deploy model to inference service
   - Versioned deployments
   - Health checks

6. **update_redis_cache**: Warm up Redis cache
   - Caches top 1000 items
   - Non-critical task

**Manual Trigger**:
```bash
# Via Airflow UI: Click on DAG -> Trigger DAG
# Or via CLI:
airflow dags trigger tenant_model_training -c '{"tenant_id": "acme-corp"}'
```

### 2. Data Quality Check (`data_quality_check`)

**Schedule**: Every 6 hours

**Purpose**: Monitor and validate data quality across all tenants

**Tasks**:
1. **check_data_completeness**: Validate required fields
   - Checks for NULL values
   - Validates field presence
   - Calculates completeness percentage

2. **check_data_freshness**: Verify data timeliness
   - user_interactions: < 24 hours old
   - items: < 7 days old
   - model_training_runs: < 24 hours old

3. **check_for_anomalies**: Detect data anomalies
   - Duplicate interactions
   - Orphaned records
   - Unusual interaction patterns
   - Invalid interaction types

4. **decide_alert_needed**: Evaluate if alerting is needed
   - Branches based on severity
   - Routes to send_alert or skip_alert

5. **send_alert**: Send alert to monitoring service
   - HTTP POST to monitoring service
   - Falls back to Airflow logs if service unavailable

**Manual Trigger**:
```bash
airflow dags trigger data_quality_check
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- MinIO client (`mc`) for bucket initialization
- At least 4GB RAM available for services

### Quick Start

1. **Start all services**:
```bash
bash scripts/start-local.sh
```

This will:
- Start PostgreSQL, Redis, MinIO, Kafka
- Initialize MinIO buckets
- Create Kafka topics
- Start Airflow webserver and scheduler

2. **Access Airflow UI**:
```
URL: http://localhost:8080
Username: admin
Password: admin
```

3. **Verify DAGs**:
- Navigate to DAGs page
- You should see `tenant_model_training` and `data_quality_check`
- Both DAGs should be paused initially

### Manual DAG Execution

#### Trigger Training Pipeline

1. Open Airflow UI (http://localhost:8080)
2. Click on `tenant_model_training` DAG
3. Click "Trigger DAG" button (play icon)
4. Add configuration (optional):
   ```json
   {
     "tenant_id": "my-tenant"
   }
   ```
5. Click "Trigger"

#### Monitor Execution

1. Click on the running DAG instance
2. View the **Graph** tab to see task dependencies
3. Click on individual tasks to view:
   - **Logs**: Detailed execution logs
   - **XCom**: Data passed between tasks
   - **Task Instance Details**: Runtime information

### View Logs

**Via Airflow UI**:
1. Click on DAG
2. Click on task
3. Click "Log" button

**Via Docker**:
```bash
# Airflow webserver logs
docker-compose logs -f airflow-webserver

# Airflow scheduler logs
docker-compose logs -f airflow-scheduler

# All logs
docker-compose logs -f
```

### Troubleshooting

#### DAGs Not Showing Up

1. Check DAG file syntax:
```bash
docker-compose exec airflow-webserver airflow dags list
```

2. View DAG import errors:
```bash
docker-compose exec airflow-webserver airflow dags list-import-errors
```

3. Restart scheduler:
```bash
docker-compose restart airflow-scheduler
```

#### Task Failures

1. **Check task logs** in Airflow UI
2. **Retry the task**: Click task -> "Clear" -> "Run"
3. **Check dependencies**:
   - PostgreSQL is running
   - MinIO is accessible
   - ML Engine API is available

#### Connection Issues

Airflow needs connections configured for:
- `postgres_default`: PostgreSQL connection
- `minio_default`: MinIO S3 connection

**Configure connections**:
1. Admin -> Connections
2. Add/Edit connections as needed

Example MinIO connection:
- **Conn Id**: `minio_default`
- **Conn Type**: `Amazon Web Services`
- **Extra**:
  ```json
  {
    "aws_access_key_id": "minioadmin",
    "aws_secret_access_key": "minioadmin",
    "endpoint_url": "http://minio:9000"
  }
  ```

## Configuration

### Environment Variables

Set in `docker-compose.yml`:

```yaml
AIRFLOW__CORE__EXECUTOR: LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__CORE__FERNET_KEY: <your-fernet-key>
AIRFLOW__CORE__LOAD_EXAMPLES: False
AIRFLOW__WEBSERVER__SECRET_KEY: <your-secret-key>
```

### DAG Configuration

Edit DAG files in `control-plane/airflow/dags/`:

**Training schedule**:
```python
schedule_interval='0 2 * * *',  # Daily at 2 AM
```

**Data quality schedule**:
```python
schedule_interval='0 */6 * * *',  # Every 6 hours
```

## Production Considerations

### Scaling

For production deployments:

1. **Use CeleryExecutor or KubernetesExecutor** instead of LocalExecutor
2. **Add worker nodes** for parallel task execution
3. **Use external PostgreSQL** with proper backup/HA
4. **Use Redis or RabbitMQ** as message broker for Celery

### Monitoring

1. **Enable StatsD** for metrics collection
2. **Configure alerting** via email/Slack/PagerDuty
3. **Set up log aggregation** (ELK stack, Datadog, etc.)
4. **Monitor resource usage** (CPU, memory, disk)

### Security

1. **Change default credentials** for Airflow
2. **Use secrets backend** (AWS Secrets Manager, Vault)
3. **Enable RBAC** for access control
4. **Use TLS/SSL** for all connections
5. **Restrict network access** to Airflow UI

### Backup

1. **Backup Airflow metadata DB** (PostgreSQL)
2. **Version control DAG files** (Git)
3. **Backup logs** to object storage
4. **Document recovery procedures**

## Development

### Adding New DAGs

1. Create Python file in `control-plane/airflow/dags/`
2. Define DAG with proper configuration
3. Implement tasks as Python functions
4. Test locally using `airflow dags test`
5. Commit to version control

Example DAG structure:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'my_new_dag',
    default_args=default_args,
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
)

def my_task(**context):
    print("Hello from my task!")
    return "Success"

task = PythonOperator(
    task_id='my_task',
    python_callable=my_task,
    dag=dag,
)
```

### Testing DAGs

```bash
# List all DAGs
airflow dags list

# Test DAG import
airflow dags test my_dag 2025-01-01

# Test specific task
airflow tasks test my_dag my_task 2025-01-01

# Validate DAG structure
airflow dags show my_dag
```

## API Integration

The DAGs interact with the following services via HTTP:

### ML Engine API
- **Base URL**: `http://ml-engine:8000`
- **Endpoints**:
  - `POST /api/v1/train` - Start training job
  - `GET /api/v1/jobs/{job_id}/status` - Check job status
  - `POST /api/v1/index/build` - Build FAISS index

### Inference Service API
- **Base URL**: `http://inference-service:8001`
- **Endpoints**:
  - `POST /api/v1/deploy` - Deploy model
  - `POST /api/v1/cache/warm` - Warm up cache

### Monitoring Service API
- **Base URL**: `http://monitoring-service:8002`
- **Endpoints**:
  - `POST /api/v1/alerts` - Send alert

## Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [DAG Writing Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#writing-a-dag)

## Support

For issues or questions:
1. Check Airflow logs for error details
2. Review DAG documentation in task `doc_md`
3. Consult this README
4. Check Airflow community resources

## License

Proprietary - Internal use only
