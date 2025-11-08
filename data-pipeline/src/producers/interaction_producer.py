"""
Interaction data producer for streaming ingestion
Supports both Kafka and Redis Streams (for MVP)
"""
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class InteractionProducer:
    """Producer for streaming interaction data"""

    def __init__(self, mode: str = "redis"):
        """
        Initialize producer

        Args:
            mode: "kafka" or "redis" (default: redis for MVP)
        """
        self.mode = mode

        if mode == "kafka":
            self._init_kafka()
        elif mode == "redis":
            self._init_redis()
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _init_kafka(self):
        """Initialize Kafka producer"""
        try:
            from kafka import KafkaProducer

            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers.split(","),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info(f"Kafka producer initialized: {bootstrap_servers}")

        except Exception as e:
            logger.error(f"Error initializing Kafka producer: {e}")
            raise

    def _init_redis(self):
        """Initialize Redis Streams producer"""
        try:
            import redis

            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))

            self.producer = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False
            )
            logger.info(f"Redis Streams producer initialized: {redis_host}:{redis_port}")

        except Exception as e:
            logger.error(f"Error initializing Redis producer: {e}")
            raise

    def send_interaction(self, tenant_id: str, interaction: Dict) -> bool:
        """
        Send interaction event to stream

        Args:
            tenant_id: Tenant identifier
            interaction: Interaction data

        Returns:
            True if successful
        """
        try:
            message = {
                'tenant_id': tenant_id,
                'user_id': interaction['user_id'],
                'item_id': interaction['item_id'],
                'interaction_type': interaction['interaction_type'],
                'timestamp': interaction.get('timestamp', datetime.now().isoformat()),
                'context': interaction.get('context', {}),
                'metadata': interaction.get('metadata', {})
            }

            if self.mode == "kafka":
                return self._send_kafka(tenant_id, message)
            else:
                return self._send_redis(tenant_id, message)

        except Exception as e:
            logger.error(f"Error sending interaction: {e}", exc_info=True)
            return False

    def _send_kafka(self, tenant_id: str, message: Dict) -> bool:
        """Send to Kafka topic"""
        try:
            topic = "interactions-raw"
            self.producer.send(
                topic,
                key=tenant_id,
                value=message
            )
            self.producer.flush()
            return True

        except Exception as e:
            logger.error(f"Error sending to Kafka: {e}")
            return False

    def _send_redis(self, tenant_id: str, message: Dict) -> bool:
        """Send to Redis Stream"""
        try:
            stream_key = f"interactions-raw:{tenant_id}"
            self.producer.xadd(
                stream_key,
                {
                    'data': json.dumps(message).encode('utf-8')
                },
                maxlen=100000  # Keep last 100k messages
            )
            return True

        except Exception as e:
            logger.error(f"Error sending to Redis: {e}")
            return False

    def send_batch(self, tenant_id: str, interactions: list) -> int:
        """
        Send batch of interactions

        Args:
            tenant_id: Tenant identifier
            interactions: List of interaction dictionaries

        Returns:
            Number of successful sends
        """
        success_count = 0

        for interaction in interactions:
            if self.send_interaction(tenant_id, interaction):
                success_count += 1

        logger.info(f"Sent {success_count}/{len(interactions)} interactions for tenant {tenant_id}")
        return success_count

    def close(self):
        """Close producer connection"""
        if self.mode == "kafka":
            self.producer.close()
            logger.info("Kafka producer closed")
        else:
            self.producer.close()
            logger.info("Redis producer closed")
