# Metrics Catalog - Embedding Recommender SaaS

Complete reference of all metrics exposed by the platform and where they appear in dashboards.

## Table of Contents
- [System Metrics](#system-metrics)
- [Backend API Metrics](#backend-api-metrics)
- [ML Engine Metrics](#ml-engine-metrics)
- [Data Pipeline Metrics](#data-pipeline-metrics)
- [Infrastructure Metrics](#infrastructure-metrics)
- [Dashboard Mapping](#dashboard-mapping)

---

## System Metrics

### Container Metrics (via cAdvisor)

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `container_cpu_usage_seconds_total` | Counter | container_name | Total CPU time consumed | System Health |
| `container_memory_usage_bytes` | Gauge | container_name | Current memory usage | System Health |
| `container_fs_reads_bytes_total` | Counter | container_name | Total filesystem reads | System Health |
| `container_fs_writes_bytes_total` | Counter | container_name | Total filesystem writes | System Health |
| `container_network_receive_bytes_total` | Counter | container_name | Total network bytes received | System Health |
| `container_network_transmit_bytes_total` | Counter | container_name | Total network bytes sent | System Health |
| `container_spec_memory_limit_bytes` | Gauge | container_name | Memory limit for container | System Health |

### Node Metrics (via Node Exporter)

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `node_cpu_seconds_total` | Counter | mode, cpu | CPU time per mode | System Health |
| `node_memory_MemAvailable_bytes` | Gauge | - | Available memory | System Health |
| `node_filesystem_avail_bytes` | Gauge | device, mountpoint | Available disk space | System Health |
| `node_filesystem_size_bytes` | Gauge | device, mountpoint | Total disk space | System Health |
| `node_network_receive_bytes_total` | Counter | device | Network bytes received | System Health |
| `node_network_transmit_bytes_total` | Counter | device | Network bytes sent | System Health |

---

## Backend API Metrics

### HTTP Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `http_requests_total` | Counter | method, endpoint, status, tenant_id | Total HTTP requests | API Performance, Business |
| `http_request_duration_seconds` | Histogram | method, endpoint | Request duration in seconds | API Performance |
| `http_requests_in_progress` | Gauge | method, endpoint | Currently processing requests | API Performance |
| `http_request_size_bytes` | Histogram | method, endpoint | Request payload size | API Performance |
| `http_response_size_bytes` | Histogram | method, endpoint | Response payload size | API Performance |

**Example PromQL Queries**:
```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### Recommendation Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `recommendations_served_total` | Counter | tenant_id, algorithm | Total recommendations served | Business Metrics |
| `recommendation_quality` | Gauge | tenant_id, metric | Quality score (NDCG, etc.) | Business Metrics |
| `recommendation_duration_seconds` | Histogram | tenant_id, algorithm | Time to generate recommendations | API Performance |
| `recommendation_items_count` | Histogram | tenant_id | Number of items recommended | Business Metrics |

**Example PromQL Queries**:
```promql
# Recommendations per hour
sum(increase(recommendations_served_total[1h]))

# Top tenants by recommendations
topk(10, sum(rate(recommendations_served_total[5m])) by (tenant_id))
```

### Cache Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `cache_hits_total` | Counter | cache_type | Total cache hits | API Performance |
| `cache_misses_total` | Counter | cache_type | Total cache misses | API Performance |
| `cache_operations_duration_seconds` | Histogram | cache_type, operation | Cache operation duration | API Performance |
| `cache_size_bytes` | Gauge | cache_type | Current cache size | System Health |
| `cache_evictions_total` | Counter | cache_type, reason | Total evictions | System Health |

**Example PromQL Queries**:
```promql
# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Low cache hit rate alert
(rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))) < 0.7
```

### Rate Limiting Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `api_requests_rate_limited_total` | Counter | tenant_id, endpoint | Requests blocked by rate limiter | API Performance |
| `rate_limit_quota_remaining` | Gauge | tenant_id | Remaining quota for tenant | Business Metrics |

---

## ML Engine Metrics

### Training Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `training_job_status` | Gauge | job_id, tenant_id | Job status (0=failed, 1=running, 2=pending, 3=completed) | ML Engine |
| `training_job_duration_seconds` | Histogram | tenant_id, model_type | Training duration | ML Engine |
| `training_job_completed_total` | Counter | tenant_id, model_type | Completed training jobs | ML Engine |
| `training_job_failures_total` | Counter | tenant_id, reason | Failed training jobs | ML Engine |
| `training_dataset_size` | Gauge | tenant_id, job_id | Size of training dataset | ML Engine |
| `training_iterations_total` | Counter | tenant_id, job_id | Total training iterations | ML Engine |

**Example PromQL Queries**:
```promql
# Training jobs in last hour
increase(training_job_completed_total[1h])

# Training failure rate
rate(training_job_failures_total[5m]) / rate(training_job_completed_total[5m])
```

### Model Quality Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `model_quality_ndcg_at_10` | Gauge | tenant_id, model_version | NDCG@10 score | ML Engine |
| `model_quality_map_at_10` | Gauge | tenant_id, model_version | MAP@10 score | ML Engine |
| `model_quality_precision_at_10` | Gauge | tenant_id, model_version | Precision@10 | ML Engine |
| `model_quality_recall_at_10` | Gauge | tenant_id, model_version | Recall@10 | ML Engine |
| `model_quality_auc` | Gauge | tenant_id, model_version | Area Under Curve | ML Engine |
| `model_version_deployed` | Gauge | tenant_id, model_name | Currently deployed version number | ML Engine |

**Quality Thresholds**:
- NDCG@10: > 0.3 (good), > 0.5 (excellent)
- MAP@10: > 0.25 (good), > 0.4 (excellent)
- Precision@10: > 0.2 (good), > 0.35 (excellent)

### Inference Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `ml_engine_requests_total` | Counter | endpoint, tenant_id | Total ML requests | ML Engine |
| `embedding_generation_duration_seconds` | Histogram | model_name | Time to generate embeddings | ML Engine |
| `faiss_search_duration_seconds` | Histogram | index_type | FAISS search latency | ML Engine |
| `embedding_cache_hits_total` | Counter | - | Embedding cache hits | ML Engine |
| `embedding_cache_misses_total` | Counter | - | Embedding cache misses | ML Engine |
| `embedding_cache_last_update_timestamp` | Gauge | - | Last cache update time | ML Engine |
| `ml_engine_errors_total` | Counter | error_type | ML processing errors | ML Engine |

**Example PromQL Queries**:
```promql
# Embedding cache hit rate
rate(embedding_cache_hits_total[5m]) / (rate(embedding_cache_hits_total[5m]) + rate(embedding_cache_misses_total[5m]))

# FAISS p95 latency
histogram_quantile(0.95, rate(faiss_search_duration_seconds_bucket[5m]))

# ML request rate by operation
sum(rate(ml_engine_requests_total[5m])) by (endpoint)
```

---

## Data Pipeline Metrics

### ETL Job Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `etl_job_duration_seconds` | Histogram | job_name | ETL job execution time | (Future dashboard) |
| `etl_job_failures_total` | Counter | job_name, reason | Failed ETL jobs | (Alerts) |
| `etl_records_processed_total` | Counter | job_name, source | Records processed | (Future dashboard) |
| `etl_records_skipped_total` | Counter | job_name, reason | Records skipped | (Future dashboard) |
| `etl_data_quality_score` | Gauge | job_name, metric | Data quality score | (Future dashboard) |

### Kafka Consumer Metrics

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `kafka_consumer_lag` | Gauge | topic, partition, consumer_group | Consumer lag in messages | (Alerts) |
| `kafka_messages_consumed_total` | Counter | topic, consumer_group | Total messages consumed | (Future dashboard) |
| `kafka_processing_errors_total` | Counter | topic, error_type | Processing errors | (Alerts) |
| `kafka_processing_duration_seconds` | Histogram | topic | Message processing time | (Future dashboard) |
| `kafka_consumer_offset` | Gauge | topic, partition | Current consumer offset | (Future dashboard) |

**Example PromQL Queries**:
```promql
# Consumer lag alert
kafka_consumer_lag > 10000

# Processing rate
rate(kafka_messages_consumed_total[5m])
```

---

## Infrastructure Metrics

### Database Metrics (via postgres_exporter)

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `pg_up` | Gauge | - | PostgreSQL is up (1=up, 0=down) | System Health |
| `pg_stat_database_numbackends` | Gauge | database | Active connections | System Health |
| `pg_stat_database_tup_fetched` | Counter | database | Rows fetched | API Performance |
| `pg_stat_database_tup_inserted` | Counter | database | Rows inserted | (Future dashboard) |
| `pg_stat_database_tup_updated` | Counter | database | Rows updated | (Future dashboard) |
| `pg_stat_database_tup_deleted` | Counter | database | Rows deleted | (Future dashboard) |
| `pg_database_size_bytes` | Gauge | database | Database size | System Health |

### Redis Metrics (via redis_exporter)

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `redis_up` | Gauge | - | Redis is up (1=up, 0=down) | System Health |
| `redis_connected_clients` | Gauge | - | Connected clients | System Health |
| `redis_used_memory_bytes` | Gauge | - | Memory usage | System Health |
| `redis_keyspace_hits_total` | Counter | - | Cache hits | API Performance |
| `redis_keyspace_misses_total` | Counter | - | Cache misses | API Performance |
| `redis_commands_processed_total` | Counter | cmd | Commands processed | (Future dashboard) |

### Service Health

| Metric Name | Type | Labels | Description | Dashboard |
|-------------|------|--------|-------------|-----------|
| `up` | Gauge | job, instance | Target is reachable (1=up, 0=down) | System Health, All |

---

## Dashboard Mapping

### System Health Dashboard

**Metrics Used**:
```
container_cpu_usage_seconds_total
container_memory_usage_bytes
container_spec_memory_limit_bytes
node_filesystem_avail_bytes
node_filesystem_size_bytes
container_network_receive_bytes_total
container_network_transmit_bytes_total
up{job=~"backend-api|ml-engine|data-pipeline|postgres|redis"}
```

**Panels**:
- Service status (up/down)
- CPU usage (rate calculation)
- Memory usage (percentage)
- Disk space (percentage)
- Network I/O

---

### API Performance Dashboard

**Metrics Used**:
```
http_requests_total
http_request_duration_seconds
http_request_size_bytes
http_response_size_bytes
cache_hits_total
cache_misses_total
pg_stat_database_tup_fetched
redis_keyspace_hits_total
redis_keyspace_misses_total
```

**Panels**:
- Request rate by endpoint
- Latency percentiles (p50, p95, p99)
- Error rate by status code
- Top 10 slowest endpoints
- Request/response size
- Cache hit rate
- Database queries
- Active connections

---

### ML Engine Performance Dashboard

**Metrics Used**:
```
training_job_status
training_job_completed_total
training_job_failures_total
model_quality_ndcg_at_10
model_quality_map_at_10
model_quality_precision_at_10
model_quality_recall_at_10
embedding_cache_hits_total
embedding_cache_misses_total
faiss_search_duration_seconds
embedding_generation_duration_seconds
ml_engine_requests_total
model_version_deployed
```

**Panels**:
- Training job status (gauge with color mapping)
- Model quality (NDCG@10 stat)
- Cache hit rate
- FAISS search latency
- Request rate by operation
- Model quality over time
- Training jobs (completed/failed)
- Cache performance
- Model versions
- Embedding generation latency

---

### Business Metrics Dashboard

**Metrics Used**:
```
recommendations_served_total
api_requests_total
revenue_total_usd (mock)
tenant_status
```

**Panels**:
- Recommendations served (last hour)
- API calls (last hour)
- Active tenants count
- Revenue (mock)
- Recommendations over time
- API calls by tenant
- Top 10 tenants by usage
- Tenant usage summary table
- Revenue by tenant
- Tenant growth
- Endpoint usage distribution

---

## Metric Naming Conventions

### Counters
- Suffix: `_total`
- Example: `http_requests_total`, `cache_hits_total`
- Always increasing values

### Gauges
- No suffix or `_current`
- Example: `memory_usage_bytes`, `training_job_status`
- Can go up or down

### Histograms
- Suffix: `_seconds`, `_bytes`
- Auto-generates: `_bucket`, `_sum`, `_count`
- Example: `http_request_duration_seconds`

### Summaries
- Suffix: `_seconds`
- Auto-generates: quantiles, `_sum`, `_count`
- Example: `api_latency_seconds`

---

## Label Best Practices

### Required Labels
- `tenant_id`: For multi-tenancy
- `service`: Service name
- `environment`: dev/staging/prod

### Optional Labels
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: API endpoint path
- `status`: HTTP status code
- `error_type`: Error classification
- `algorithm`: Recommendation algorithm used
- `model_version`: Model version identifier

### Labels to Avoid
- High cardinality: `user_id`, `request_id`, `session_id`
- Timestamps: Use metric timestamp instead
- Dynamic values: UUIDs, random IDs

---

## Example Integration

### Python (FastAPI)

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'tenant_id']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

cache_hits = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_type']
)

# Use in code
@app.get("/recommendations")
async def get_recommendations(tenant_id: str):
    start = time.time()

    # Check cache
    cached = cache.get(f"rec:{tenant_id}")
    if cached:
        cache_hits.labels(cache_type="recommendations").inc()
        requests_total.labels(
            method="GET",
            endpoint="/recommendations",
            status="200",
            tenant_id=tenant_id
        ).inc()
        request_duration.labels(
            method="GET",
            endpoint="/recommendations"
        ).observe(time.time() - start)
        return cached

    # Generate recommendations
    results = generate_recommendations(tenant_id)

    requests_total.labels(
        method="GET",
        endpoint="/recommendations",
        status="200",
        tenant_id=tenant_id
    ).inc()

    request_duration.labels(
        method="GET",
        endpoint="/recommendations"
    ).observe(time.time() - start)

    return results
```

---

## Query Examples

### Performance Queries

```promql
# Top 10 slowest endpoints (p95)
topk(10,
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
  )
)

# Error rate by endpoint
sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)
/ sum(rate(http_requests_total[5m])) by (endpoint)

# Request rate spike detection
rate(http_requests_total[1m]) > 2 * avg_over_time(rate(http_requests_total[1m])[5m:1m])
```

### Business Queries

```promql
# Daily active tenants
count(count_over_time(api_requests_total[24h])) by (tenant_id)

# Revenue per tenant (if revenue_total_usd exists)
sum(increase(revenue_total_usd[24h])) by (tenant_id)

# Recommendations per tenant per hour
sum(increase(recommendations_served_total[1h])) by (tenant_id)
```

### ML Queries

```promql
# Average model quality across all tenants
avg(model_quality_ndcg_at_10)

# Cache efficiency
sum(rate(embedding_cache_hits_total[5m]))
/ (sum(rate(embedding_cache_hits_total[5m])) + sum(rate(embedding_cache_misses_total[5m])))

# Training success rate
sum(rate(training_job_completed_total[1h]))
/ (sum(rate(training_job_completed_total[1h])) + sum(rate(training_job_failures_total[1h])))
```

---

## Metric Retention

### Prometheus
- **Raw data**: 15 days
- **Aggregated (1m)**: 30 days
- **Aggregated (5m)**: 90 days

### Recommended Recording Rules

```yaml
# Save CPU to pre-calculate common queries
groups:
  - name: aggregations
    interval: 30s
    rules:
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)

      - record: job:http_request_duration:p95
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))

      - record: tenant:recommendations:rate1h
        expr: sum(rate(recommendations_served_total[1h])) by (tenant_id)
```

---

**Last Updated**: 2025-01-07
**Version**: 1.0.0
**Total Metrics Documented**: 80+
