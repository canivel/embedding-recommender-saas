#!/bin/bash
# Initialize Kafka topics for the Embedding Recommender SaaS platform

set -e

echo "Initializing Kafka topics..."

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 10

KAFKA_CONTAINER="kafka"
KAFKA_BROKER="localhost:9092"

# Function to create a topic if it doesn't exist
create_topic() {
  local topic=$1
  local partitions=$2
  local replication=$3

  echo "Creating topic '$topic' with $partitions partitions..."

  docker exec $KAFKA_CONTAINER kafka-topics.sh \
    --create \
    --if-not-exists \
    --bootstrap-server $KAFKA_BROKER \
    --topic $topic \
    --partitions $partitions \
    --replication-factor $replication \
    --config retention.ms=604800000 \
    --config compression.type=lz4
}

# Create topics
# Format: create_topic <topic-name> <partitions> <replication-factor>

echo ""
echo "Creating user interaction topics..."
create_topic "user-interactions" 6 1
create_topic "user-interactions-processed" 6 1

echo ""
echo "Creating model training topics..."
create_topic "training-jobs" 3 1
create_topic "training-results" 3 1

echo ""
echo "Creating embedding topics..."
create_topic "embedding-requests" 6 1
create_topic "embedding-responses" 6 1

echo ""
echo "Creating recommendation topics..."
create_topic "recommendation-requests" 6 1
create_topic "recommendation-responses" 6 1

echo ""
echo "Creating monitoring topics..."
create_topic "metrics" 3 1
create_topic "alerts" 3 1

echo ""
echo "Creating data pipeline topics..."
create_topic "data-ingestion" 6 1
create_topic "data-validation" 3 1

echo ""
echo "Kafka topics created successfully!"
echo ""
echo "Listing all topics:"
docker exec $KAFKA_CONTAINER kafka-topics.sh \
  --list \
  --bootstrap-server $KAFKA_BROKER

echo ""
echo "Topic details:"
docker exec $KAFKA_CONTAINER kafka-topics.sh \
  --describe \
  --bootstrap-server $KAFKA_BROKER
