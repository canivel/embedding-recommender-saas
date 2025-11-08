# Observability Stack Testing Guide

This guide walks you through testing the observability infrastructure to ensure everything is working correctly.

## Prerequisites

- Docker and Docker Compose installed
- All services started: `docker-compose up -d`
- Allow 1-2 minutes for services to fully initialize

## Quick Health Check

```bash
# Check all observability services are running
docker-compose ps prometheus grafana loki jaeger

# Expected output: All services should show "Up" status
```

## Test 1: Prometheus Metrics Collection

### Verify Prometheus is Running

```bash
# Check Prometheus health
curl http://localhost:9090/-/healthy

# Expected: "Prometheus is Healthy."
```

### Check Scrape Targets

1. Open http://localhost:9090/targets
2. Verify all targets show "UP" status:
   - prometheus (self-monitoring)
   - backend-api (if running)
   - ml-engine (if running)
   - data-pipeline (if running)

### Run Test Queries

Navigate to http://localhost:9090/graph and test these queries:

```promql
# Check if any services are up
up

# Expected: Should show 1 for each running service

# Query scrape duration
scrape_duration_seconds

# Expected: Should show scrape times (typically < 0.1s)
```

### Test Alert Rules

```bash
# Check alert rules are loaded
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'

# Expected: Should list: critical_alerts, warning_alerts, info_alerts
```

## Test 2: Grafana Dashboards

### Access Grafana

1. Open http://localhost:3001
2. Login with:
   - Username: `admin`
   - Password: `admin`
3. Skip password change (or set new password)

### Verify Datasources

1. Navigate to Configuration → Data Sources
2. Verify three datasources exist:
   - **Prometheus** (default) - Status: Working ✓
   - **Loki** - Status: Working ✓
   - **Jaeger** - Status: Working ✓

### Test Each Dashboard

#### System Health Dashboard

1. Navigate to Dashboards → Browse → Team Zeta → System Health
2. Verify panels show data:
   - CPU Usage per Service (should show prometheus metrics)
   - Memory Usage per Service
   - Service Status

**Note**: Some panels may show "No data" if application services aren't running yet.

#### API Performance Dashboard

1. Navigate to Team Zeta → API Performance
2. Panels will show data once backend-api is instrumented and receiving traffic

**Generate Test Traffic** (if backend-api is running):
```bash
# Send test requests
for i in {1..10}; do
  curl http://localhost:8000/health
  sleep 1
done
```

#### ML Engine Performance Dashboard

1. Navigate to Team Zeta → ML Engine Performance
2. Verify dashboard structure:
   - Training Job Status panel
   - Model Quality Metrics panel
   - Cache Hit Rate panel
   - FAISS Search Latency panel

#### Business Metrics Dashboard

1. Navigate to Team Zeta → Business Metrics
2. Verify all panels render (data appears after services generate metrics)

## Test 3: Loki Log Aggregation

### Verify Loki is Running

```bash
# Check Loki health
curl http://localhost:3100/ready

# Expected: "ready"
```

### Query Logs via API

```bash
# Query recent logs (if any exist)
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="varlogs"}' \
  --data-urlencode 'limit=10' | jq .

# Expected: JSON response with log entries
```

### Test Logging via Grafana

1. Open Grafana → Explore
2. Select **Loki** datasource from dropdown
3. Enter query: `{job="varlogs"}`
4. Click "Run query"
5. Should see log entries (if Promtail is collecting logs)

### Send Test Log Entry

```bash
# Send a test log to Loki
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [
      {
        "stream": {
          "service": "test",
          "level": "info"
        },
        "values": [
          ["'$(date +%s%N)'", "Test log message from testing guide"]
        ]
      }
    ]
  }'

# Query back the test log
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="test"}' \
  --data-urlencode 'limit=5' | jq .
```

## Test 4: Jaeger Distributed Tracing

### Verify Jaeger is Running

```bash
# Check Jaeger health
curl http://localhost:14269/

# Expected: HTML response from Jaeger UI
```

### Access Jaeger UI

1. Open http://localhost:16686
2. Verify Jaeger UI loads successfully

### Test Trace Collection (Python Example)

Create a test script to send a trace:

```python
# test_tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
import time

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Create a test trace
tracer = trace.get_tracer("test-service")
with tracer.start_as_current_span("test-operation") as span:
    span.set_attribute("test.attribute", "test-value")
    time.sleep(0.1)
    print("Trace sent to Jaeger!")

# Give time for export
time.sleep(2)
```

Run the test:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
python test_tracing.py
```

Then check Jaeger UI:
1. Select "test-service" from Service dropdown
2. Click "Find Traces"
3. Should see the test trace

## Test 5: Alert Rules

### Check Alert Rule Syntax

```bash
# Validate alert rules (if promtool is available)
docker-compose exec prometheus promtool check rules /etc/prometheus/rules/alert-rules.yml

# Expected: No errors, "SUCCESS" message
```

### View Active Alerts

1. Navigate to http://localhost:9090/alerts
2. Should see all defined alert rules
3. Most should show "Inactive" state (green)
4. Some may show "Pending" or "Firing" if conditions are met

### Trigger Test Alert

Simulate a service down alert:

```bash
# Stop a service temporarily
docker-compose stop backend-api

# Wait 1-2 minutes, then check alerts
# Navigate to http://localhost:9090/alerts
# ServiceDown alert should transition to "Pending" then "Firing"

# Restart service
docker-compose start backend-api

# Alert should resolve after 1-2 minutes
```

## Test 6: Example Instrumentation Code

### Test Logging Configuration

```bash
cd observability/examples/

# Run the logging example
python logging_config.py

# Expected: JSON-formatted logs printed to stdout
```

Example output:
```json
{"timestamp": "2025-01-07T16:30:45.123Z", "level": "INFO", "logger": "__main__", "message": "Service started", ...}
{"timestamp": "2025-01-07T16:30:45.125Z", "level": "DEBUG", "logger": "__main__", "message": "Debug information", ...}
```

### Test Tracing Configuration

```bash
# Run the tracing example
python tracing_config.py

# Expected: "Tracing examples completed. View traces at http://localhost:16686"
```

Check Jaeger:
1. Open http://localhost:16686
2. Select "example-service"
3. Find traces for "process_user_request" and "fetch_recommendations"

## Test 7: End-to-End Integration Test

This test verifies the complete observability pipeline.

### 1. Start Application Services

```bash
# Start backend-api with instrumentation
docker-compose up -d backend-api ml-engine data-pipeline
```

### 2. Generate Test Traffic

```bash
# Send requests to generate metrics, logs, and traces
for i in {1..50}; do
  curl -X POST http://localhost:8000/api/v1/recommendations \
    -H "Content-Type: application/json" \
    -H "X-Tenant-ID: test-tenant-123" \
    -d '{"user_id": "user-'$i'", "count": 10}'
  sleep 0.5
done
```

### 3. Verify Metrics in Prometheus

```promql
# Query request count
sum(increase(http_requests_total{job="backend-api"}[5m]))

# Should show ~50 requests
```

### 4. Verify Logs in Loki

In Grafana Explore with Loki datasource:
```logql
{service="backend-api"} | json | tenant_id="test-tenant-123"
```

Should show request logs.

### 5. Verify Traces in Jaeger

1. Open http://localhost:16686
2. Select "backend-api" service
3. Click "Find Traces"
4. Should see traces for the 50 requests

### 6. Check Grafana Dashboards

All dashboards should now show active data:
- **API Performance**: Request rate, latency graphs
- **Business Metrics**: API calls, recommendations count
- **System Health**: CPU/memory usage from services

## Common Issues and Solutions

### Issue: Prometheus shows targets as "DOWN"

**Solution:**
```bash
# Check if service is running
docker-compose ps backend-api

# Check service logs
docker-compose logs backend-api

# Verify /metrics endpoint exists
curl http://localhost:8000/metrics
```

### Issue: Grafana shows "No data"

**Solutions:**
1. Check time range (top-right) - ensure it covers data period
2. Verify datasource connection (Configuration → Data Sources)
3. Check if metrics exist in Prometheus:
   ```bash
   curl http://localhost:9090/api/v1/query?query=up
   ```

### Issue: Jaeger shows no traces

**Solutions:**
1. Verify tracing is initialized in application
2. Check Jaeger agent port is accessible:
   ```bash
   docker-compose logs jaeger | grep -i "started"
   ```
3. Ensure service is sending traces to correct host:port

### Issue: Loki not receiving logs

**Solutions:**
1. Check Loki is running:
   ```bash
   docker-compose ps loki
   ```
2. Verify Promtail configuration (if using)
3. Check logs are in correct format (JSON recommended)

## Performance Benchmarks

After running tests, verify observability overhead is acceptable:

### Prometheus Metrics
- **Scrape duration**: Should be < 100ms per target
- **Query response time**: Should be < 1s for simple queries
- **Memory usage**: Typically 200-500MB for this stack

Check in Prometheus:
```promql
# Scrape duration
scrape_duration_seconds

# Prometheus memory usage
process_resident_memory_bytes{job="prometheus"}
```

### Grafana Dashboard Load Time
- **First load**: < 5 seconds (including data fetch)
- **Refresh**: < 2 seconds

### Loki Query Performance
- **Simple query**: < 1 second
- **Complex query with filters**: < 5 seconds

### Jaeger Trace Retrieval
- **Find traces**: < 2 seconds
- **Trace detail view**: < 1 second

## Success Criteria

All tests pass if:

- ✅ Prometheus scrapes all configured targets successfully
- ✅ All Grafana datasources connect successfully
- ✅ All 4 dashboards load without errors
- ✅ Loki receives and stores log entries
- ✅ Jaeger collects and displays traces
- ✅ Alert rules load without syntax errors
- ✅ Example instrumentation code runs successfully
- ✅ End-to-end test shows data in all three pillars (metrics, logs, traces)

## Next Steps

After successful testing:

1. **Integrate into CI/CD**: Add observability stack startup to your CI pipeline
2. **Set up Alerting**: Configure Alertmanager with Slack/PagerDuty webhooks
3. **Create Custom Dashboards**: Build dashboards for your specific use cases
4. **Instrument Your Code**: Use the examples to add observability to your services
5. **Set up SLOs**: Define and track Service Level Objectives

## Resources

- [Prometheus Testing](https://prometheus.io/docs/prometheus/latest/getting_started/)
- [Grafana Testing](https://grafana.com/docs/grafana/latest/setup-grafana/installation/)
- [Loki Testing](https://grafana.com/docs/loki/latest/send-data/)
- [Jaeger Testing](https://www.jaegertracing.io/docs/latest/getting-started/)

---

**Last Updated**: 2025-01-07
**Version**: 1.0.0
