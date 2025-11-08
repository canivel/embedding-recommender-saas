"""Kafka producer for publishing events."""
import json
import logging
from typing import Any, Dict, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from ..config import settings

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """Kafka producer client for publishing events."""

    def __init__(self):
        """Initialize Kafka producer."""
        self.producer = None
        self._connect()

    def _connect(self):
        """Connect to Kafka."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
            logger.info(f"Connected to Kafka at {settings.kafka_bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None

    def send_event(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Send an event to a Kafka topic.

        Args:
            topic: Kafka topic name
            value: Event payload (will be serialized to JSON)
            key: Optional message key for partitioning

        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logger.warning("Kafka producer not connected, attempting reconnect...")
            self._connect()
            if not self.producer:
                return False

        try:
            future = self.producer.send(topic, value=value, key=key)
            # Wait for the send to complete (synchronous)
            record_metadata = future.get(timeout=10)
            logger.debug(
                f"Sent event to {topic} (partition {record_metadata.partition}, "
                f"offset {record_metadata.offset})"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to send event to {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending event to {topic}: {e}")
            return False

    def send_interaction_event(self, interaction: Dict[str, Any]) -> bool:
        """
        Send an interaction event.

        Args:
            interaction: Interaction data

        Returns:
            True if successful, False otherwise
        """
        return self.send_event(
            topic=settings.kafka_topic_interactions,
            value=interaction,
            key=interaction.get('user_id')
        )

    def send_item_event(self, item: Dict[str, Any]) -> bool:
        """
        Send an item catalog event.

        Args:
            item: Item data

        Returns:
            True if successful, False otherwise
        """
        return self.send_event(
            topic=settings.kafka_topic_items,
            value=item,
            key=item.get('item_id')
        )

    def send_features_event(self, features: Dict[str, Any]) -> bool:
        """
        Send a features processed event.

        Args:
            features: Features data

        Returns:
            True if successful, False otherwise
        """
        return self.send_event(
            topic=settings.kafka_topic_features,
            value=features,
            key=features.get('entity_id')
        )

    def send_training_data_event(self, training_data: Dict[str, Any]) -> bool:
        """
        Send a training data event.

        Args:
            training_data: Training data sample

        Returns:
            True if successful, False otherwise
        """
        return self.send_event(
            topic=settings.kafka_topic_training,
            value=training_data,
            key=training_data.get('user_id')
        )

    def flush(self):
        """Flush any pending messages."""
        if self.producer:
            self.producer.flush()

    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Global instance
kafka_producer = KafkaProducerClient()
