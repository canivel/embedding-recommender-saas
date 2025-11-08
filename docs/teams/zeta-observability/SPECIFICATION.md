# Team Zeta: Observability & Analytics

## Mission
Build comprehensive monitoring, logging, tracing, and analytics infrastructure to ensure system reliability and provide business insights.

## Technology Stack
- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) or Loki
- **Tracing**: Jaeger or OpenTelemetry
- **Alerting**: AlertManager + PagerDuty
- **Business Analytics**: ClickHouse or BigQuery
- **Product Analytics**: Mixpanel or Amplitude
- **APM** (optional): DataDog or New Relic

## Architecture

### Three Pillars of Observability

#### 1. Metrics (Prometheus + Grafana)

**Key Metrics:**

**System Metrics:**
```promql
# CPU usage by service
container_cpu_usage_seconds_total{namespace="production"}

# Memory usage
container_memory_usage_bytes{namespace="production"}

# Disk I/O
rate(container_fs_reads_bytes_total[5m])
```

**Application Metrics:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Latency (p95, p99)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Cache hit rate
cache_hits_total / (cache_hits_total + cache_misses_total)
```

**Business Metrics:**
```promql
# Recommendations served per tenant
rate(recommendations_served_total{tenant_id="..."}[1h])

# Model quality (NDCG@10)
ml_recommendation_quality{metric="ndcg_10", tenant_id="..."}

# API calls per plan
sum by (plan) (rate(api_calls_total[1h]))
```

**Grafana Dashboards:**

1. **System Health Dashboard**
   - Service status (green/yellow/red)
   - CPU, memory, disk usage
   - Network I/O
   - Pod restarts

2. **API Performance Dashboard**
   - Request rate per endpoint
   - Latency (p50, p95, p99)
   - Error rate by status code
   - Top 10 slowest endpoints

3. **ML Engine Dashboard**
   - Training job status
   - Model performance over time
   - Embedding cache hit rate
   - ANN search latency

4. **Business Dashboard**
   - Active tenants
   - API calls by plan
   - Revenue metrics (MRR, ARR)
   - Top tenants by usage

5. **Tenant-Specific Dashboard**
   - Per-tenant API usage
   - Model quality metrics
   - Data freshness
   - Quota utilization

#### 2. Logging (ELK Stack)

**Log Format (Structured JSON):**
```json
{
  "timestamp": "2025-01-07T10:30:45.123Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "abc123def456",
  "span_id": "xyz789",
  "tenant_id": "tenant_001",
  "user_id": "user_456",
  "endpoint": "/api/v1/recommendations",
  "method": "POST",
  "status_code": 200,
  "latency_ms": 45,
  "message": "Request processed successfully",
  "context": {
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1",
    "api_key_id": "key_789"
  }
}
```

**Logstash Pipeline:**
```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  json {
    source => "message"
  }

  # Parse timestamps
  date {
    match => ["timestamp", "ISO8601"]
  }

  # Add GeoIP for IP addresses
  geoip {
    source => "context.ip_address"
  }

  # Anonymize PII
  mutate {
    remove_field => ["user_id", "context.ip_address"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{service}-%{+YYYY.MM.dd}"
  }
}
```

**Kibana Queries:**
```
# Errors in last hour
level:ERROR AND timestamp:[now-1h TO now]

# Slow requests (>1s)
latency_ms:>1000

# Failed login attempts
endpoint:"/api/v1/auth/login" AND status_code:401

# Tenant-specific logs
tenant_id:"tenant_001" AND level:ERROR
```

#### 3. Tracing (Jaeger)

**Instrumentation Example:**
```python
# backend-api instrumentation
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger import JaegerExporter

tracer = trace.get_tracer(__name__)

@app.post("/api/v1/recommendations")
async def get_recommendations(request: RecommendationRequest):
    with tracer.start_as_current_span("get_recommendations") as span:
        span.set_attribute("tenant_id", request.tenant_id)
        span.set_attribute("user_id", request.user_id)

        # Call ML engine
        with tracer.start_as_current_span("ml_engine_call"):
            recommendations = await ml_client.get_recommendations(...)

        # Log usage
        with tracer.start_as_current_span("log_usage"):
            await log_api_usage(...)

        return recommendations
```

**Trace Example:**
```
Request: POST /api/v1/recommendations [150ms]
├─ authenticate [5ms]
├─ ml_engine_call [120ms]
│  ├─ get_user_embedding [10ms]
│  │  └─ redis_get [8ms]
│  ├─ ann_search [80ms]
│  │  └─ faiss_search [78ms]
│  └─ rerank [30ms]
└─ log_usage [15ms]
   └─ postgres_insert [12ms]
```

## Alerting Rules

### Critical Alerts (Page Immediately)

```yaml
# prometheus/alerts.yaml
groups:
  - name: critical
    rules:
      - alert: ServiceDown
        expr: up{job="backend-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5% for {{ $labels.service }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "p95 latency > 1s for {{ $labels.endpoint }}"

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"
```

### Warning Alerts (Slack Notification)

```yaml
  - name: warnings
    rules:
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage > 85% for {{ $labels.pod }}"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space < 15% on {{ $labels.instance }}"

      - alert: ModelTrainingFailed
        expr: training_job_status{status="failed"} > 0
        labels:
          severity: warning
        annotations:
          summary: "Training job failed for tenant {{ $labels.tenant_id }}"
```

### AlertManager Configuration

```yaml
# alertmanager.yaml
global:
  resolve_timeout: 5m
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  receiver: 'slack-default'
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-oncall'
    - match:
        severity: warning
      receiver: 'slack-engineering'

receivers:
  - name: 'pagerduty-oncall'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

  - name: 'slack-engineering'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#engineering-alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'slack-default'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#general-alerts'
```

## Business Analytics (ClickHouse)

### Schema for Usage Analytics

```sql
-- clickhouse/schema.sql
CREATE TABLE api_usage (
    timestamp DateTime,
    tenant_id String,
    api_key_id String,
    endpoint String,
    method String,
    status_code UInt16,
    latency_ms UInt32,
    request_size_bytes UInt32,
    response_size_bytes UInt32,
    date Date DEFAULT toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (tenant_id, timestamp);

-- Materialized view for daily aggregates
CREATE MATERIALIZED VIEW api_usage_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (tenant_id, endpoint, date)
AS SELECT
    tenant_id,
    endpoint,
    date,
    count() as request_count,
    avg(latency_ms) as avg_latency_ms,
    quantile(0.95)(latency_ms) as p95_latency_ms,
    sum(request_size_bytes) as total_request_bytes
FROM api_usage
GROUP BY tenant_id, endpoint, date;
```

### Analytics Queries

```sql
-- Top 10 tenants by API usage
SELECT tenant_id, sum(request_count) as total_requests
FROM api_usage_daily
WHERE date >= today() - 30
GROUP BY tenant_id
ORDER BY total_requests DESC
LIMIT 10;

-- Error rate by endpoint
SELECT
    endpoint,
    countIf(status_code >= 500) / count() * 100 as error_rate_percent
FROM api_usage
WHERE date >= today() - 7
GROUP BY endpoint
HAVING error_rate_percent > 1
ORDER BY error_rate_percent DESC;

-- Latency trend over time
SELECT
    date,
    quantile(0.50)(latency_ms) as p50,
    quantile(0.95)(latency_ms) as p95,
    quantile(0.99)(latency_ms) as p99
FROM api_usage
WHERE date >= today() - 30
GROUP BY date
ORDER BY date;
```

## SLI/SLO/SLA Framework

### Service Level Indicators (SLIs)
- **Availability**: Percentage of successful requests (status != 5xx)
- **Latency**: p95 latency < 100ms
- **Throughput**: Requests per second
- **Error Rate**: Percentage of failed requests

### Service Level Objectives (SLOs)
- **Availability**: 99.9% (43 minutes downtime/month)
- **Latency**: p95 < 100ms for 99% of requests
- **Error Rate**: < 0.1% error rate

### Service Level Agreements (SLAs)
- **Starter Plan**: 99% uptime
- **Pro Plan**: 99.9% uptime
- **Enterprise Plan**: 99.95% uptime + priority support

### Error Budget Tracking

```promql
# Remaining error budget for the month
1 - (
  (sum(rate(http_requests_total{status=~"5.."}[30d])) /
   sum(rate(http_requests_total[30d])))
  / (1 - 0.999)  # 99.9% SLO
)
```

## Cost Analytics

### Dashboard Metrics
- AWS/GCP cost per service
- Cost per API call
- Cost per tenant
- Cost trend over time
- Cost optimization recommendations

### ClickHouse Query
```sql
SELECT
    date,
    service,
    sum(cost_usd) as daily_cost,
    sum(cost_usd) / sum(api_calls) as cost_per_call
FROM cost_data
WHERE date >= today() - 30
GROUP BY date, service
ORDER BY date DESC;
```

## Deployment

### Kubernetes Manifests

```yaml
# prometheus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

## Success Criteria
- Mean time to detection (MTTD) < 5 minutes
- Mean time to resolution (MTTR) < 1 hour
- Zero missed critical alerts
- Grafana dashboard load time < 3s
- Log search query time < 5s
- 100% trace coverage for critical paths

## Development Workflow

### Phase 1 (Weeks 1-2)
- [ ] Prometheus + Grafana setup
- [ ] Basic dashboards (system, API)
- [ ] Critical alerting rules
- [ ] PagerDuty integration

### Phase 2 (Weeks 3-4)
- [ ] ELK stack deployment
- [ ] Structured logging implementation
- [ ] Jaeger tracing setup
- [ ] Slack alerting

### Phase 3 (Weeks 5-6)
- [ ] ClickHouse analytics
- [ ] Business dashboards
- [ ] SLO tracking
- [ ] Cost analytics
