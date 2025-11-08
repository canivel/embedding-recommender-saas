#!/bin/bash
# Start all services for local development

set -e

echo "========================================="
echo "Starting Embedding Recommender SaaS"
echo "Local Development Environment"
echo "========================================="
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
  echo "Error: docker-compose is not installed"
  exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Stop any existing containers
echo "Stopping any existing containers..."
docker-compose down

# Pull latest images (optional)
# echo "Pulling latest images..."
# docker-compose pull

# Start infrastructure services first
echo ""
echo "Starting infrastructure services..."
echo "  - PostgreSQL (port 5432)"
echo "  - Redis (port 6379)"
echo "  - MinIO (port 9000, console: 9001)"
echo "  - Kafka + Zookeeper (port 9092)"
echo ""

docker-compose up -d postgres redis minio zookeeper kafka

# Wait for infrastructure to be ready
echo "Waiting for infrastructure services to be ready..."
sleep 10

# Initialize MinIO buckets
echo ""
echo "Initializing MinIO buckets..."
if [ -f "$SCRIPT_DIR/init-minio.sh" ]; then
  bash "$SCRIPT_DIR/init-minio.sh"
else
  echo "Warning: init-minio.sh not found, skipping MinIO initialization"
fi

# Wait a bit more for Kafka to stabilize
sleep 5

# Initialize Kafka topics
echo ""
echo "Initializing Kafka topics..."
if [ -f "$SCRIPT_DIR/init-kafka.sh" ]; then
  bash "$SCRIPT_DIR/init-kafka.sh"
else
  echo "Warning: init-kafka.sh not found, skipping Kafka initialization"
fi

# Start Airflow services
echo ""
echo "Starting Airflow services..."
echo "  - Airflow Webserver (port 8080)"
echo "  - Airflow Scheduler"
echo ""

# Initialize Airflow database
echo "Initializing Airflow database..."
docker-compose run --rm airflow-init

# Start Airflow webserver and scheduler
docker-compose up -d airflow-webserver airflow-scheduler

# Wait for Airflow to be ready
echo "Waiting for Airflow to be ready..."
sleep 10

# Show running containers
echo ""
echo "========================================="
echo "Services Started Successfully!"
echo "========================================="
echo ""
docker-compose ps

echo ""
echo "========================================="
echo "Service URLs:"
echo "========================================="
echo "Airflow UI:        http://localhost:8080"
echo "  Username:        admin"
echo "  Password:        admin"
echo ""
echo "MinIO Console:     http://localhost:9001"
echo "  Access Key:      minioadmin"
echo "  Secret Key:      minioadmin"
echo ""
echo "PostgreSQL:        localhost:5432"
echo "  Database:        embeddings_saas"
echo "  Username:        postgres"
echo "  Password:        postgres"
echo ""
echo "Redis:             localhost:6379"
echo "Kafka:             localhost:9092"
echo ""
echo "========================================="
echo "Quick Commands:"
echo "========================================="
echo "View logs:         docker-compose logs -f [service]"
echo "Stop all:          bash scripts/stop-local.sh"
echo "Restart service:   docker-compose restart [service]"
echo ""
echo "Trigger training:  Open Airflow UI and trigger 'tenant_model_training' DAG"
echo "View data quality: Open Airflow UI and view 'data_quality_check' DAG"
echo ""
