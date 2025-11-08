# Team Eta: Data Ingestion Pipeline

## Mission
Build robust data ingestion pipelines to collect, validate, transform, and prepare customer data for ML training and serving.

## Technology Stack
- **Streaming**: Apache Kafka or AWS Kinesis
- **Batch Processing**: Apache Airflow + PySpark
- **Data Quality**: Great Expectations
- **Data Storage**: S3 + Parquet/Delta Lake
- **Schema Registry**: Confluent Schema Registry or AWS Glue
- **Language**: Python 3.11+

## Architecture

### Data Flow

```
Customer Data Sources
    ├─ CSV Upload (API)
    ├─ Streaming API (Kafka)
    ├─ Webhook Events
    └─ SDK Integration
         ↓
    Ingestion Layer
    ├─ Validation
    ├─ Deduplication
    └─ Enrichment
         ↓
    Raw Data Lake (S3)
    ├─ JSON (streaming)
    └─ Parquet (batch)
         ↓
    ETL Pipeline (Airflow + Spark)
    ├─ Feature Engineering
    ├─ Data Quality Checks
    └─ Partitioning
         ↓
    Training Data (S3)
    └─ Parquet (optimized for ML)
```

## Components

### 1. Streaming Ingestion (Kafka)

**Topics:**
- `interactions-raw`: Raw user-item interactions
- `items-catalog`: Item metadata updates
- `events-clickstream`: Real-time clickstream data

**Producer Example:**
```python
# src/producers/interaction_producer.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_interaction(tenant_id: str, interaction: dict):
    message = {
        'tenant_id': tenant_id,
        'user_id': interaction['user_id'],
        'item_id': interaction['item_id'],
        'interaction_type': interaction['type'],
        'timestamp': interaction['timestamp'],
        'context': interaction.get('context', {})
    }

    producer.send(
        'interactions-raw',
        key=tenant_id.encode('utf-8'),
        value=message
    )
    producer.flush()
```

**Consumer Example:**
```python
# src/consumers/interaction_consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'interactions-raw',
    bootstrap_servers=['kafka:9092'],
    group_id='data-pipeline-consumer',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    interaction = message.value
    tenant_id = message.key.decode('utf-8')

    # Validate
    if validate_interaction(interaction):
        # Write to S3
        write_to_s3(tenant_id, interaction)
    else:
        # Log validation error
        log_validation_error(interaction)
```

### 2. Batch Upload (CSV)

**Upload Endpoint:**
```python
# src/api/upload.py
from fastapi import UploadFile, HTTPException
import pandas as pd

@router.post("/internal/data/upload-csv")
async def upload_csv(
    tenant_id: str,
    file: UploadFile,
    data_type: str  # "interactions" or "items"
):
    try:
        # Read CSV
        df = pd.read_csv(file.file)

        # Validate schema
        required_columns = get_required_columns(data_type)
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(400, "Missing required columns")

        # Validate data
        errors = validate_dataframe(df, data_type)
        if errors:
            return {"status": "validation_failed", "errors": errors}

        # Write to S3
        s3_path = f"s3://bucket/{tenant_id}/raw/{data_type}/{date}.parquet"
        df.to_parquet(s3_path, index=False)

        return {
            "status": "success",
            "rows_accepted": len(df),
            "s3_path": s3_path
        }

    except Exception as e:
        raise HTTPException(500, str(e))
```

### 3. Data Validation (Great Expectations)

**Expectation Suite:**
```python
# src/validation/expectations.py
import great_expectations as ge

def create_interaction_expectations():
    suite = ge.DataContext().create_expectation_suite("interactions")

    # Required columns exist
    suite.expect_column_to_exist("user_id")
    suite.expect_column_to_exist("item_id")
    suite.expect_column_to_exist("interaction_type")
    suite.expect_column_to_exist("timestamp")

    # Data types
    suite.expect_column_values_to_be_of_type("timestamp", "datetime64")
    suite.expect_column_values_to_be_of_type("user_id", "string")

    # Value constraints
    suite.expect_column_values_to_be_in_set(
        "interaction_type",
        ["view", "click", "purchase", "like", "dislike"]
    )

    # No nulls in critical fields
    suite.expect_column_values_to_not_be_null("user_id")
    suite.expect_column_values_to_not_be_null("item_id")

    # Timestamp within reasonable range
    suite.expect_column_values_to_be_between(
        "timestamp",
        min_value="2020-01-01",
        max_value="2030-01-01"
    )

    return suite

def validate_data(df: pd.DataFrame, suite_name: str):
    context = ge.DataContext()
    suite = context.get_expectation_suite(suite_name)

    batch = ge.dataset.PandasDataset(df)
    results = batch.validate(expectation_suite=suite)

    return results
```

### 4. ETL Pipeline (Airflow + Spark)

**Airflow DAG:**
```python
# dags/prepare_training_data.py
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

with DAG(
    'prepare_training_data',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
) as dag:

    # Task 1: Extract raw interactions
    extract_interactions = SparkSubmitOperator(
        task_id='extract_interactions',
        application='jobs/extract_interactions.py',
        conf={
            'spark.driver.memory': '4g',
            'spark.executor.memory': '4g',
        },
        application_args=[
            '--tenant-id', '{{ params.tenant_id }}',
            '--start-date', '{{ ds }}',
            '--end-date', '{{ next_ds }}'
        ]
    )

    # Task 2: Feature engineering
    feature_engineering = SparkSubmitOperator(
        task_id='feature_engineering',
        application='jobs/feature_engineering.py',
        application_args=[
            '--tenant-id', '{{ params.tenant_id }}',
            '--input', 's3://bucket/{{ params.tenant_id }}/raw/',
            '--output', 's3://bucket/{{ params.tenant_id }}/features/'
        ]
    )

    # Task 3: Data quality checks
    quality_checks = PythonOperator(
        task_id='quality_checks',
        python_callable=run_quality_checks,
        op_args=['{{ params.tenant_id }}']
    )

    # Task 4: Create training samples
    create_training_data = SparkSubmitOperator(
        task_id='create_training_data',
        application='jobs/create_training_data.py',
        application_args=[
            '--tenant-id', '{{ params.tenant_id }}',
            '--negative-sampling-ratio', '4',  # 1 positive : 4 negatives
            '--output', 's3://bucket/{{ params.tenant_id }}/training_data/'
        ]
    )

    extract_interactions >> feature_engineering >> quality_checks >> create_training_data
```

**Spark Job (Feature Engineering):**
```python
# jobs/feature_engineering.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("FeatureEngineering").getOrCreate()

def create_features(tenant_id: str, input_path: str, output_path: str):
    # Read raw interactions
    interactions = spark.read.parquet(f"{input_path}/interactions/")

    # User features
    user_features = interactions.groupBy("user_id").agg(
        F.count("*").alias("total_interactions"),
        F.countDistinct("item_id").alias("unique_items"),
        F.avg("rating").alias("avg_rating"),
        F.max("timestamp").alias("last_interaction")
    )

    # Item features
    item_features = interactions.groupBy("item_id").agg(
        F.count("*").alias("popularity"),
        F.countDistinct("user_id").alias("unique_users"),
        F.avg("rating").alias("avg_rating")
    )

    # Recency features (user's last N interactions)
    window = Window.partitionBy("user_id").orderBy(F.desc("timestamp"))
    recent_interactions = interactions.withColumn("rank", F.row_number().over(window)) \
        .filter(F.col("rank") <= 50)

    # Write features
    user_features.write.parquet(f"{output_path}/user_features/", mode="overwrite")
    item_features.write.parquet(f"{output_path}/item_features/", mode="overwrite")
    recent_interactions.write.parquet(f"{output_path}/recent_interactions/", mode="overwrite")

    spark.stop()
```

**Create Training Data (Negative Sampling):**
```python
# jobs/create_training_data.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def create_training_samples(tenant_id: str, negative_ratio: int = 4):
    spark = SparkSession.builder.appName("CreateTrainingData").getOrCreate()

    # Read positive interactions (clicks, purchases, etc.)
    positive_interactions = spark.read.parquet(f"s3://bucket/{tenant_id}/raw/interactions/") \
        .filter(F.col("interaction_type").isin(["click", "purchase", "like"])) \
        .select("user_id", "item_id") \
        .withColumn("label", F.lit(1.0))

    # Get all items
    all_items = spark.read.parquet(f"s3://bucket/{tenant_id}/raw/items/") \
        .select("item_id")

    # Negative sampling: randomly sample items user hasn't interacted with
    negative_interactions = positive_interactions.select("user_id").distinct() \
        .crossJoin(all_items) \
        .join(
            positive_interactions.select("user_id", "item_id"),
            on=["user_id", "item_id"],
            how="left_anti"  # Anti-join to exclude positive interactions
        ) \
        .sample(fraction=negative_ratio / 100.0) \
        .limit(len(positive_interactions) * negative_ratio) \
        .withColumn("label", F.lit(0.0))

    # Combine positive and negative samples
    training_data = positive_interactions.union(negative_interactions)

    # Write to S3
    training_data.write.parquet(
        f"s3://bucket/{tenant_id}/training_data/{date}/",
        mode="overwrite",
        partitionBy=["label"]
    )

    spark.stop()
```

### 5. Data Schema Management

**Schema Registry (Avro):**
```json
{
  "type": "record",
  "name": "Interaction",
  "namespace": "com.embeddings.saas",
  "fields": [
    {"name": "user_id", "type": "string"},
    {"name": "item_id", "type": "string"},
    {"name": "interaction_type", "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "context", "type": ["null", {
      "type": "record",
      "name": "Context",
      "fields": [
        {"name": "device_type", "type": ["null", "string"], "default": null},
        {"name": "location", "type": ["null", "string"], "default": null},
        {"name": "session_id", "type": ["null", "string"], "default": null}
      ]
    }], "default": null}
  ]
}
```

### 6. Data Quality Monitoring

**Metrics to Track:**
- Data freshness (time since last update)
- Completeness (% of required fields filled)
- Validity (% passing validation)
- Uniqueness (duplicate rate)
- Consistency (cross-field checks)

**Data Quality Dashboard:**
```python
# src/monitoring/data_quality.py
from prometheus_client import Gauge

data_freshness_hours = Gauge(
    'data_freshness_hours',
    'Hours since last data ingestion',
    ['tenant_id', 'data_type']
)

data_completeness_percent = Gauge(
    'data_completeness_percent',
    'Percentage of complete records',
    ['tenant_id', 'data_type']
)

data_validity_percent = Gauge(
    'data_validity_percent',
    'Percentage of valid records',
    ['tenant_id', 'data_type']
)

def calculate_data_quality(tenant_id: str):
    # Check freshness
    last_update = get_last_update_time(tenant_id)
    hours_since = (datetime.now() - last_update).total_seconds() / 3600
    data_freshness_hours.labels(tenant_id=tenant_id, data_type='interactions').set(hours_since)

    # Check completeness
    df = read_latest_data(tenant_id)
    completeness = (1 - df.isnull().sum().sum() / df.size) * 100
    data_completeness_percent.labels(tenant_id=tenant_id, data_type='interactions').set(completeness)

    # Check validity
    validation_results = validate_data(df)
    validity = validation_results.success_percent
    data_validity_percent.labels(tenant_id=tenant_id, data_type='interactions').set(validity)
```

### 7. Privacy & Compliance

**GDPR Compliance:**
```python
# src/compliance/gdpr.py
def delete_user_data(user_id: str, tenant_id: str):
    """Delete all user data (GDPR right to erasure)."""

    # Delete from Kafka (not possible, wait for retention)
    # Mark for deletion in S3
    s3_client = boto3.client('s3')
    objects = s3_client.list_objects_v2(
        Bucket='embeddings-saas-data',
        Prefix=f'{tenant_id}/raw/interactions/'
    )

    for obj in objects.get('Contents', []):
        # Read, filter, rewrite
        df = pd.read_parquet(f"s3://{obj['Key']}")
        df_filtered = df[df['user_id'] != user_id]
        df_filtered.to_parquet(f"s3://{obj['Key']}", index=False)

    # Delete from training data
    training_data_path = f"s3://bucket/{tenant_id}/training_data/"
    # Similar filtering process

    # Log deletion for audit
    log_gdpr_deletion(user_id, tenant_id)

def export_user_data(user_id: str, tenant_id: str) -> dict:
    """Export all user data (GDPR right to data portability)."""

    data = {
        'interactions': [],
        'embeddings': [],
        'recommendations_received': []
    }

    # Collect from S3
    df = pd.read_parquet(f"s3://bucket/{tenant_id}/raw/interactions/")
    user_interactions = df[df['user_id'] == user_id]
    data['interactions'] = user_interactions.to_dict('records')

    # Collect embeddings from Redis
    embedding = redis_client.get(f"{tenant_id}:embedding:{user_id}")
    if embedding:
        data['embeddings'] = pickle.loads(embedding).tolist()

    return data
```

## Data Retention Policy

| Data Type | Hot Storage | Warm Storage | Cold Storage | Deletion |
|-----------|-------------|--------------|--------------|----------|
| Raw interactions | 7 days (S3 Standard) | 30 days (S3 IA) | 90 days (Glacier) | After 1 year |
| Training data | 30 days | 90 days | 1 year | After 2 years |
| Model artifacts | 30 days | 6 months | 1 year | After 2 years |
| Logs | 7 days | 30 days | 90 days | After 1 year |

## Success Criteria
- Data ingestion latency < 5 seconds (streaming)
- Data quality score > 95%
- Zero data loss
- GDPR deletion within 24 hours
- Training data refresh every 6 hours

## Development Workflow

### Phase 1 (Weeks 1-2)
- [ ] Kafka setup (or Kinesis)
- [ ] CSV upload endpoint
- [ ] Basic validation
- [ ] S3 data lake structure

### Phase 2 (Weeks 3-4)
- [ ] Airflow DAGs
- [ ] Spark feature engineering
- [ ] Great Expectations validation
- [ ] Schema registry

### Phase 3 (Weeks 5-6)
- [ ] Negative sampling logic
- [ ] Data quality monitoring
- [ ] GDPR compliance tools
- [ ] Performance optimization
