#!/bin/bash
# Stop all services

set -e

echo "========================================="
echo "Stopping Embedding Recommender SaaS"
echo "Local Development Environment"
echo "========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Stop all services
echo "Stopping all Docker containers..."
docker-compose down

echo ""
echo "========================================="
echo "All services stopped successfully!"
echo "========================================="
echo ""
echo "To remove volumes (WARNING: deletes all data):"
echo "  docker-compose down -v"
echo ""
echo "To start services again:"
echo "  bash scripts/start-local.sh"
echo ""
