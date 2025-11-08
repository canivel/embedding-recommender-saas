#!/bin/bash
# Initialize MinIO buckets for the Embedding Recommender SaaS platform

set -e

echo "Initializing MinIO buckets..."

# Wait for MinIO to be ready
until mc alias set minio http://localhost:9000 minioadmin minioadmin; do
  echo "Waiting for MinIO to be ready..."
  sleep 2
done

echo "MinIO is ready!"

# Create buckets
buckets=(
  "embeddings-training-data"
  "embeddings-models"
  "embeddings-indices"
  "embeddings-raw-data"
  "embeddings-processed-data"
)

for bucket in "${buckets[@]}"; do
  if mc ls minio/$bucket 2>/dev/null; then
    echo "Bucket '$bucket' already exists"
  else
    echo "Creating bucket '$bucket'..."
    mc mb minio/$bucket
    echo "Setting public policy for bucket '$bucket'..."
    mc anonymous set download minio/$bucket
  fi
done

echo "MinIO initialization complete!"
echo ""
echo "Created buckets:"
mc ls minio
