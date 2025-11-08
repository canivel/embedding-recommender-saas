# Observability Stack - Quick Reference Card

## URLs & Access

| Component | URL | Username | Password |
|-----------|-----|----------|----------|
| Grafana | http://localhost:3000 | admin | admin123 |
| Prometheus | http://localhost:9090 | - | - |
| Jaeger | http://localhost:16686 | - | - |
| AlertManager | http://localhost:9093 | - | - |
| Loki | http://localhost:3100 | - | - |

## Commands

### Start/Stop Stack
```bash
cd observability
docker-compose up -d       # Start all services
docker-compose down        # Stop all services
docker-compose logs -f     # Watch logs
docker-compose ps          # Check status
docker-compose down -v     # Reset volumes
```

### Verify Services
```bash
# Check all targets are up
curl http://localhost:9090/api/v1/targets

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=up'

# Check Loki status
curl http://localhost:3100/ready

# Check Jaeger
curl http://localhost:14269/
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend-api
docker-compose logs -f ml-engine
```

## Key Dashboards

### System Health
**Path**: http://localhost:3000/d/system-health

**Key Panels**:
- Service Status (4 status indicators)
- CPU Usage (line chart)
- Memory Usage (line chart)
- Disk Space (line chart)
- Network I/O (stacked area)

**Key Metrics**:
```promql
up{job="backend-api"}
rate(container_cpu_usage_seconds_total[5m])
container_memory_usage_bytes
node_filesystem_avail_bytes / node_filesystem_size_bytes
```

### API Performance
**Path**: http://localhost:3000/d/api-performance

**Key Panels**:
- Request Rate by Endpoint
- Latency (p50, p95, p99)
- Error Rate
- Response Code Distribution
- Top 10 Slowest Endpoints

**Key Metrics**:
```promql
sum by (endpoint) (rate(http_requests_total[5m]))
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le))
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

## Alert Rules

### Critical Alerts (Page via PagerDuty + Slack)
| Alert | Condition | When to Act |
|-------|-----------|-------------|
| ServiceDown | Service unreachable 1min | Immediately |
| HighErrorRate | >5% errors for 5min | Check service logs |
| HighLatencyP95 | >1s for 10min | Scale up or optimize |
| DatabaseDown | DB unreachable 1min | Check DB status |
| RedisDown | Cache down 1min | Check Redis |

### Warning Alerts (Slack notification)
| Alert | Condition | Action |
|-------|-----------|--------|
| HighMemoryUsage | >85% for 10min | Plan scaling |
| HighCPUUsage | >80% for 10min | Monitor performance |
| DiskSpaceLow | <15% for 5min | Free up space |
| CacheHitRateLow | <70% for 10min | Investigate cache |

## PromQL Cheat Sheet

### Basic Queries
```promql
# Service status
up{job="backend-api"}

# Request rate (per second)
rate(http_requests_total[5m])

# Error rate (percentage)
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes / (1024^3)  # In GB

# Disk usage
node_filesystem_used_bytes / node_filesystem_size_bytes
```

### Aggregation
```promql
# Sum over labels
sum by (endpoint) (metric)

# Top 10
topk(10, sum by (endpoint) (metric))

# By service
sum by (service) (metric)
```

## Log Queries (Loki)

### Basic Format
```
{service="backend-api", level="ERROR"}
```

### JSON Parsing
```
{service="backend-api"} | json
```

### Filtering
```
{service="backend-api", level="ERROR"} | latency_ms > 1000
```

### Specific Tenant
```
{tenant_id="tenant_001"} | json | status_code >= 500
```

## Trace Queries (Jaeger)

1. Open http://localhost:16686
2. Select Service: `backend-api` or `ml-engine`
3. Select Operation: e.g., `POST /api/v1/recommendations`
4. Set time range
5. Click "Find Traces"

### Trace Inspection
- Click trace to see spans
- Hover over spans to see duration
- Look for long spans (bottlenecks)
- Check span logs and errors

## Metrics Endpoints

### Service Metrics
```bash
# Backend API
curl http://localhost:8000/metrics

# ML Engine
curl http://localhost:8001/metrics

# System (Node Exporter)
curl http://localhost:9100/metrics

# cAdvisor
curl http://localhost:8080/metrics
```

## Configuration Files

| File | Purpose | Edit For |
|------|---------|----------|
| `prometheus/prometheus.yml` | Scrape targets | Add new exporters |
| `prometheus/alert-rules.yml` | Alert rules | Add new alerts |
| `alertmanager/alertmanager.yml` | Alert routing | Slack/PagerDuty URLs |
| `loki/loki-config.yml` | Log storage | Retention settings |
| `grafana/provisioning/datasources.yml` | Data sources | Add Elasticsearch, etc |
| `.env` | Environment vars | Credentials, URLs |

## Common Issues

### Services Won't Start
```bash
docker-compose down -v
docker-compose up -d
docker-compose logs  # Check errors
```

### No Metrics in Prometheus
```bash
curl http://localhost:9090/api/v1/targets
# Check if targets are UP
```

### No Logs in Loki
```bash
curl http://localhost:3100/ready  # Check Loki
docker-compose logs promtail       # Check Promtail
```

### No Traces in Jaeger
```bash
# Verify UDP port is listening
netstat -ul | grep 6831
# Check Jaeger logs
docker-compose logs jaeger
```

### Grafana Dashboard Blank
```bash
# Check datasources: http://localhost:3000/datasources
# Verify Prometheus is up: http://localhost:9090
# Try manual query in Prometheus: http://localhost:9090/graph
```

## Environment Variables

Edit `.env` file:

```bash
# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin123

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_ADDRESS=redis:6379

# Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
PAGERDUTY_SERVICE_KEY=your_key_here

# Retention
PROMETHEUS_RETENTION=30d
```

## Instrumentation Checklist

For each new service:

1. **Add Libraries**
   ```bash
   pip install prometheus-client opentelemetry-api opentelemetry-exporter-jaeger
   ```

2. **Define Metrics**
   ```python
   from prometheus_client import Counter
   requests = Counter('http_requests_total', '', ['method', 'status'])
   ```

3. **Setup Logging**
   ```python
   from pythonjsonlogger import jsonlogger
   # Configure JSON logger
   ```

4. **Enable Tracing**
   ```python
   from opentelemetry.sdk.trace import TracerProvider
   trace.set_tracer_provider(TracerProvider())
   ```

5. **Expose Metrics**
   ```python
   @app.get("/metrics")
   def metrics():
       return generate_latest()
   ```

6. **Update prometheus.yml**
   ```yaml
   - job_name: 'my-service'
     static_configs:
       - targets: ['my-service:8000']
   ```

## Performance Tuning

### Reduce Cardinality (if too much data)
```yaml
# prometheus.yml
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'http_requests_total'
    action: keep  # Only keep this metric
```

### Increase Sampling in Production
```yaml
# jaeger-config.yml
sampling:
  type: probabilistic
  param: 0.1  # Sample 10% of traces
```

### Reduce Log Ingestion
```yaml
# promtail-config.yml
limits_config:
  ingestion_rate_mb: 50  # From 100MB/min
  max_entries_limit_per_second: 500  # From 1000
```

## Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Jaeger Docs](https://www.jaegertracing.io/docs/)
- [Loki Docs](https://grafana.com/docs/loki/)
- [OpenTelemetry](https://opentelemetry.io/)
- [PromQL Cheat Sheet](https://promlabs.com/blog/2020/06/15/the-anatomy-of-a-promql-query/)

## Support

**For issues**:
1. Check logs: `docker-compose logs -f`
2. Verify connectivity: `docker-compose ps`
3. Test endpoints: `curl http://localhost:PORT`
4. Check targets: http://localhost:9090/targets
5. Review docs: `observability/README.md` or `INTEGRATION_GUIDE.md`

---

**Quick Help**: For full documentation, see `README.md` and `INTEGRATION_GUIDE.md`
