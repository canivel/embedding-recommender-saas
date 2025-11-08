# Observability & Analytics Infrastructure

**Team Zeta** - Comprehensive monitoring, logging, tracing, and analytics infrastructure for the Embedding Recommender SaaS platform.

## Overview

This directory contains a complete observability stack built on industry-standard tools:

- **Prometheus**: Time-series metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards
- **Loki**: Log aggregation (lightweight alternative to ELK)
- **Promtail**: Log collection and shipping
- **Jaeger**: Distributed tracing
- **AlertManager**: Alert routing and notification management

## Quick Start

### Prerequisites

- Docker & Docker Compose (v20.10+)
- 4GB RAM available for containers
- Ports available: 3000, 3100, 6831, 6832, 9090, 9093, 14268, 16686

### 1. Setup Environment

```bash
cd observability
cp .env.example .env

# Edit .env with your configuration
# At minimum, set Slack webhook URL for alerts (optional for testing)
nano .env
```

### 2. Start the Observability Stack

```bash
docker-compose up -d
```

Verify all services are running:

```bash
docker-compose ps
```

### 3. Access the Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana** | http://localhost:3000 | Dashboards & Visualization |
| **Prometheus** | http://localhost:9090 | Metrics queries & alerts |
| **Jaeger UI** | http://localhost:16686 | Distributed tracing |
| **AlertManager** | http://localhost:9093 | Alert management |
| **Loki** | http://localhost:3100 | Log queries |

**Default Grafana Credentials**: `admin` / `admin123`

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f grafana
```

## Architecture

### Directory Structure

```
observability/
├── prometheus/
│   ├── prometheus.yml          # Scrape targets and config
│   └── alert-rules.yml         # Alerting rules
├── alertmanager/
│   └── alertmanager.yml        # Alert routing and notification
├── grafana/
│   ├── dashboards/
│   │   ├── system-health.json  # Infrastructure health
│   │   └── api-performance.json # API performance metrics
│   └── provisioning/
│       ├── datasources.yml     # Prometheus, Loki, Jaeger
│       └── dashboards.yml      # Dashboard auto-loading
├── loki/
│   ├── loki-config.yml         # Loki storage configuration
│   └── promtail-config.yml     # Log collection rules
├── jaeger/
│   └── jaeger-config.yml       # Jaeger configuration
├── examples/
│   ├── backend-api-instrumentation.py  # FastAPI example
│   ├── ml-engine-instrumentation.py    # ML Engine example
│   ├── logging_config.py               # Structured JSON logging
│   └── tracing_config.py               # Distributed tracing with Jaeger
├── docker-compose.yml          # Complete stack orchestration
├── .env.example                # Environment template
└── README.md                   # This file
```

### Data Flow

```
Services
  ↓
Prometheus (scrapes metrics)
AlertManager (processes alerts)
Promtail (collects logs) → Loki (stores/indexes)
OpenTelemetry (sends traces) → Jaeger (stores/visualizes)
  ↓
Grafana (visualizes all)
```

## Services & Components

### Prometheus (Metrics)
- **Port**: 9090
- **Function**: Scrapes metrics from service endpoints
- **Retention**: 30 days by default
- **Features**:
  - Multi-target scraping (APIs, databases, exporters)
  - Built-in alert rule evaluation
  - PromQL query language

### Grafana (Visualization)
- **Port**: 3000
- **Function**: Creates dashboards from metrics/logs/traces
- **Pre-built Dashboards**:
  - System Health: CPU, memory, disk, network
  - API Performance: Latency, error rates, throughput
  - ML Engine Performance: Model quality, cache performance, training jobs
  - Business Metrics: Revenue, recommendations, tenant usage
- **Features**:
  - Multi-datasource support
  - Alert notifications
  - Auto-provisioned dashboards

### Loki (Logging)
- **Port**: 3100
- **Function**: Log aggregation without indexing overhead
- **Benefits**:
  - Lower memory footprint than ELK
  - Uses same label scheme as Prometheus
  - Easy to correlate logs with metrics
- **Retention**: 7 days (configurable)

### Promtail (Log Collection)
- **Function**: Collects and ships logs to Loki
- **Sources**:
  - Docker container logs
  - Syslog
  - Kubernetes logs
- **Processing**: JSON parsing, field extraction, label assignment

### Jaeger (Distributed Tracing)
- **Port**: 16686 (UI), 6831 (UDP agent)
- **Function**: Traces requests across services
- **All-in-one Mode**: Single container with collector, agent, query
- **Retention**: 72 hours in-memory

### AlertManager (Alerting)
- **Port**: 9093
- **Function**: Routes alerts to appropriate channels
- **Routing**:
  - **Critical**: PagerDuty + Slack
  - **Warning**: Slack
  - **Info**: Silent
- **Features**:
  - Alert grouping and deduplication
  - Inhibition rules
  - Custom templates

## Metrics Collection

### Pre-configured Exporters

| Exporter | Target | Metrics |
|----------|--------|---------|
| **Node Exporter** | :9100 | CPU, Memory, Disk, Network |
| **cAdvisor** | :8080 | Container metrics |
| **Postgres Exporter** | :9187 | Database stats |
| **Redis Exporter** | :9121 | Cache stats |

### Application Metrics

Each service exposes metrics on its `/metrics` endpoint (e.g., `http://backend-api:8000/metrics`)

**Key Metrics**:
```
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint, status}
recommendations_served_total{tenant_id}
cache_hits_total{cache_type}
ml_model_inference_duration_seconds{tenant_id, operation}
```

## Instrumentation Guide

### For Backend APIs (FastAPI/Express)

```python
# See: examples/backend-api-instrumentation.py

from prometheus_client import Counter, Histogram
from opentelemetry import trace

# Define metrics
http_requests_total = Counter('http_requests_total', '', ['method', 'endpoint', 'status'])
http_request_duration = Histogram('http_request_duration_seconds', '', ['method', 'endpoint'])

# In request handler
with tracer.start_as_current_span("get_recommendations"):
    # Your logic here
    http_requests_total.labels(...).inc()
    http_request_duration.labels(...).observe(duration)
```

### For ML/Data Pipelines (Python)

```python
# See: examples/ml-engine-instrumentation.py

from prometheus_client import Gauge, Counter

# Track training jobs
training_job_status = Gauge('training_job_status', '', ['tenant_id', 'job_id'])
training_job_duration = Histogram('training_job_duration_seconds', '', ['tenant_id'])

# In training code
with tracer.start_as_current_span("train_model"):
    training_job_status.labels(...).set(1)  # Running
    # ... training logic ...
    training_job_duration.labels(...).observe(duration)
```

### For Node.js Services

```javascript
const promClient = require('prom-client');
const { Resource } = require('@opentelemetry/resources');
const { MeterProvider, PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');

const registry = new promClient.Registry();

// Create metrics
const httpRequests = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'endpoint', 'status'],
  registers: [registry]
});

// Use in middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequests
      .labels(req.method, req.path, res.statusCode)
      .inc();
  });
  next();
});
```

### Enabling Structured Logging

Services should output JSON logs with standard fields:

```json
{
  "timestamp": "2025-01-07T10:30:45.123Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "abc123def456",
  "span_id": "xyz789",
  "tenant_id": "tenant_001",
  "endpoint": "/api/v1/recommendations",
  "message": "Request processed successfully",
  "latency_ms": 45
}
```

### OpenTelemetry Integration

For distributed tracing, services should initialize OpenTelemetry:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
```

## Dashboards

### System Health Dashboard

**Panels**:
- Service Status (green/yellow/red)
- CPU Usage per Service
- Memory Usage per Service
- Disk Space Available
- Network I/O
- Pod/Container Restart Rate

**Queries**:
```promql
# CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes

# Disk space
node_filesystem_avail_bytes / node_filesystem_size_bytes
```

### API Performance Dashboard

**Panels**:
- Request Rate by Endpoint
- Latency (p50, p95, p99)
- Error Rate by Endpoint
- Response Code Distribution
- Top 10 Slowest Endpoints
- Top 10 Endpoints by Throughput

**Queries**:
```promql
# Request rate
sum by (endpoint) (rate(http_requests_total[5m]))

# Latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

### ML Engine Performance Dashboard

**Panels**:
- Training Job Status
- Model Quality Metrics (NDCG@10, MAP@10, Precision, Recall)
- Embedding Cache Hit Rate
- FAISS Search Latency
- ML Request Rate by Operation
- Embedding Generation Latency
- Model Version Deployed per Tenant

**Queries**:
```promql
# Model quality
model_quality_ndcg_at_10

# Cache hit rate
rate(embedding_cache_hits_total[5m]) / (rate(embedding_cache_hits_total[5m]) + rate(embedding_cache_misses_total[5m]))

# FAISS search latency
histogram_quantile(0.95, sum(rate(faiss_search_duration_seconds_bucket[5m])) by (le))
```

### Business Metrics Dashboard

**Panels**:
- Recommendations Served (Last Hour)
- API Calls by Tenant
- Active Tenants Count
- Revenue Metrics (Mock)
- Top 10 Tenants by Usage
- Tenant Growth Over Time
- API Endpoint Usage Distribution
- Tenant Usage Summary Table

**Queries**:
```promql
# Recommendations served
sum(increase(recommendations_served_total[1h]))

# Top tenants
topk(10, sum(increase(api_requests_total[1h])) by (tenant_id))

# Active tenants
count(count by (tenant_id) (api_requests_total))
```

## Alert Rules

### Critical Alerts (Page Immediately)

| Alert | Condition | Impact |
|-------|-----------|--------|
| **ServiceDown** | Service unreachable for 1min | Complete service outage |
| **HighErrorRate** | Error rate > 5% for 5min | Users seeing failures |
| **HighLatencyP95** | p95 latency > 1s for 10min | Degraded user experience |
| **DatabaseDown** | Database unreachable for 1min | All services affected |

### Warning Alerts (Slack Notification)

| Alert | Condition | Action |
|-------|-----------|--------|
| **HighMemoryUsage** | >85% for 10min | Plan scaling/optimization |
| **DiskSpaceLow** | <15% available for 5min | Cleanup/expand storage |
| **CacheHitRateLow** | <70% for 10min | Investigate cache issues |

### Alert Routing

```
Critical Alerts → PagerDuty + #zeta-critical-alerts
Warning Alerts  → #engineering-alerts
Info Alerts     → Silent (stored only)
```

## Viewing Logs

### In Grafana

1. Go to Explore → Select "Loki"
2. Query examples:
   ```
   {service="backend-api", level="ERROR"}
   {tenant_id="tenant_001"} | json
   {endpoint="/api/v1/recommendations"} | latency_ms > 1000
   ```

### In Command Line

```bash
# Watch live logs
docker-compose logs -f backend-api

# Loki queries
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="backend-api"}' | jq

# Jaeger traces
# Open http://localhost:16686
```

## Viewing Traces

1. Open Jaeger UI: http://localhost:16686
2. Select service and view traces
3. Click on trace to see span details
4. Look for latency bottlenecks

## Performance Tuning

### Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s  # Reduce for less latency, increase for less load
  evaluation_interval: 15s

# Alert rules
rule_files:
  - '/etc/prometheus/rules/*.yml'
```

### Loki

```yaml
# loki-config.yml
limits_config:
  max_entries_limit_per_second: 1000  # Increase for high volume
  ingestion_rate_mb: 100  # Limit per tenant
```

### Jaeger

```yaml
# jaeger-config.yml
sampling:
  type: const
  param: 0.1  # Sample 10% in production, 100% in dev
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs -f

# Verify network
docker network ls
docker network inspect observability_observability

# Rebuild
docker-compose down -v
docker-compose up -d
```

### Prometheus Not Scraping

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Check rules
curl http://localhost:9090/api/v1/rules

# Query metrics
curl http://localhost:9090/api/v1/query?query=up
```

### Loki Not Collecting Logs

```bash
# Check Promtail status
curl http://localhost:9080/ready

# Test log ingestion
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [
      {
        "stream": {"service": "test"},
        "values": [["'$(date +%s%N)'", "test message"]]
      }
    ]
  }'
```

### Jaeger Not Receiving Traces

```bash
# Check Jaeger UI
curl http://localhost:14269/

# Check metrics
curl http://localhost:14269/metrics | grep tracer

# Verify UDP port
netstat -ul | grep 6831
```

## Metrics Reference

### System Metrics

```
# Container metrics (from cAdvisor)
container_cpu_usage_seconds_total
container_memory_usage_bytes
container_fs_reads_bytes_total
container_fs_writes_bytes_total
container_network_receive_bytes_total
container_network_transmit_bytes_total

# Node metrics (from Node Exporter)
node_cpu_seconds_total
node_memory_MemAvailable_bytes
node_filesystem_avail_bytes
node_filesystem_size_bytes
```

### Application Metrics

```
# HTTP metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint, status}
http_requests_in_progress{method, endpoint}

# Cache metrics
cache_hits_total{cache_type}
cache_misses_total{cache_type}
cache_operations_duration_seconds{cache_type, operation}

# Database metrics
db_query_duration_seconds{query_type}
db_connection_pool_size{pool_name}

# Business metrics
recommendations_served_total{tenant_id}
recommendation_quality{tenant_id, metric}
ml_model_inference_duration_seconds{tenant_id, operation}
```

## Integration with Services

### Backend API

1. Add prometheus-client library
2. Create metrics in startup
3. Add middleware to track requests
4. Expose `/metrics` endpoint on port 8000
5. Services auto-register in prometheus.yml scrape_configs

### ML Engine

1. Add prometheus-client and opentelemetry libraries
2. Instrument training pipeline
3. Record model performance metrics
4. Enable Jaeger tracing for inference calls

### Data Pipeline

1. Add structured JSON logging
2. Track data quality metrics
3. Monitor pipeline stage durations
4. Alert on validation failures

## Success Metrics (Phase 1)

- ✅ MTTD (Mean Time To Detection): < 5 minutes
- ✅ Grafana dashboard load time: < 3 seconds
- ✅ Log search query time: < 5 seconds
- ✅ Zero missed critical alerts
- ✅ Trace coverage for API endpoints: 100%

## Next Steps (Phase 2)

- [ ] ClickHouse setup for business analytics
- [ ] SLO/SLI dashboards and tracking
- [ ] Cost analytics dashboard
- [ ] Enhanced PagerDuty/Slack integration
- [ ] Kubernetes-native monitoring

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [AlertManager Examples](https://prometheus.io/docs/alerting/latest/overview/)

## Support

For issues or questions about the observability infrastructure:

1. Check logs: `docker-compose logs -f`
2. Verify connectivity: `docker-compose ps`
3. Test endpoints directly
4. Review Prometheus targets: http://localhost:9090/targets
5. Consult Team Zeta documentation

---

**Team Zeta** - Building observability at scale
