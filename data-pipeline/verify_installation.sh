#!/bin/bash
# Verification script for data pipeline installation

set -e

echo "=========================================="
echo "DATA PIPELINE INSTALLATION VERIFICATION"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ "$python_version" > "3.11" ]] || [[ "$python_version" == "3.11"* ]]; then
    echo -e "${GREEN}✓${NC} Python $python_version (>= 3.11 required)"
else
    echo -e "${RED}✗${NC} Python $python_version (>= 3.11 required)"
    exit 1
fi

# Check UV installation
echo "Checking UV installation..."
if command -v uv &> /dev/null; then
    uv_version=$(uv --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓${NC} UV installed ($uv_version)"
else
    echo -e "${RED}✗${NC} UV not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check Docker
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✓${NC} Docker installed ($docker_version)"
else
    echo -e "${YELLOW}⚠${NC} Docker not installed (optional for local dev)"
fi

# Check directory structure
echo ""
echo "Checking directory structure..."
required_dirs=(
    "src"
    "src/api"
    "src/kafka"
    "src/etl"
    "src/validation"
    "src/storage"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/ missing"
        exit 1
    fi
done

# Check key files
echo ""
echo "Checking key files..."
required_files=(
    "pyproject.toml"
    "Dockerfile"
    "README.md"
    "QUICKSTART.md"
    "src/main.py"
    "src/config.py"
    "src/data_generator.py"
    "generate_sample_data.py"
    "test_pipeline.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file missing"
        exit 1
    fi
done

# Check if .env exists
echo ""
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
else
    echo -e "${YELLOW}⚠${NC} .env file not found (will use defaults)"
    echo "  Copy from .env.example: cp .env.example .env"
fi

# Try to import Python modules
echo ""
echo "Checking Python dependencies..."
if python3 -c "import sys; sys.path.insert(0, '.'); from src.config import settings" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Python modules can be imported"
else
    echo -e "${YELLOW}⚠${NC} Python modules cannot be imported yet"
    echo "  Install dependencies with: uv sync"
fi

# Check if services are running
echo ""
echo "Checking infrastructure services..."

# Check Kafka
if curl -s http://localhost:9092 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Kafka running on port 9092"
else
    echo -e "${YELLOW}⚠${NC} Kafka not running on port 9092"
    echo "  Start with: docker-compose up -d kafka zookeeper"
fi

# Check MinIO
if curl -s http://localhost:9000/minio/health/live >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MinIO running on port 9000"
else
    echo -e "${YELLOW}⚠${NC} MinIO not running on port 9000"
    echo "  Start with: docker-compose up -d minio"
fi

# Check if API is running
if curl -s http://localhost:8002/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Data pipeline API running on port 8002"
else
    echo -e "${YELLOW}⚠${NC} Data pipeline API not running on port 8002"
    echo "  Start with: uvicorn src.main:app --reload"
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Install dependencies: uv sync"
echo "  2. Start infrastructure: docker-compose up -d kafka minio"
echo "  3. Start API: uvicorn src.main:app --reload"
echo "  4. Generate sample data: python generate_sample_data.py --upload"
echo "  5. Visit API docs: http://localhost:8002/docs"
echo ""
