"""Kafka consumer for processing events."""
import json
import logging
from typing import Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from ..config import settings

logger = logging.getLogger(__name__)


class KafkaConsumerClient:
    """Kafka consumer client for processing events."""

    def __init__(self, group_id: str, topics: list[str]):
        """
        Initialize Kafka consumer.

        Args:
            group_id: Consumer group ID
            topics: List of topics to subscribe to
        """
        self.group_id = group_id
        self.topics = topics
        self.consumer = None
        self._connect()

    def _connect(self):
        """Connect to Kafka."""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.kafka_bootstrap_servers.split(','),
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=100,
            )
            logger.info(
                f"Connected to Kafka at {settings.kafka_bootstrap_servers} "
                f"(group: {self.group_id}, topics: {self.topics})"
            )
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.consumer = None

    def consume(
        self,
        callback: Callable[[str, dict], None],
        timeout_ms: int = 1000
    ):
        """
        Consume messages from subscribed topics.

        Args:
            callback: Function to call for each message (topic, value)
            timeout_ms: Poll timeout in milliseconds
        """
        if not self.consumer:
            logger.warning("Kafka consumer not connected, attempting reconnect...")
            self._connect()
            if not self.consumer:
                return

        try:
            while True:
                messages = self.consumer.poll(timeout_ms=timeout_ms)

                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            callback(record.topic, record.value)
                        except Exception as e:
                            logger.error(
                                f"Error processing message from {record.topic}: {e}"
                            )

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        finally:
            self.close()

    def consume_batch(
        self,
        max_messages: int = 100,
        timeout_ms: int = 5000
    ) -> dict[str, list[dict]]:
        """
        Consume a batch of messages.

        Args:
            max_messages: Maximum number of messages to consume
            timeout_ms: Total timeout in milliseconds

        Returns:
            Dictionary mapping topic to list of message values
        """
        if not self.consumer:
            logger.warning("Kafka consumer not connected, attempting reconnect...")
            self._connect()
            if not self.consumer:
                return {}

        results = {}
        messages_consumed = 0

        try:
            while messages_consumed < max_messages:
                messages = self.consumer.poll(timeout_ms=timeout_ms)

                if not messages:
                    break

                for topic_partition, records in messages.items():
                    topic = topic_partition.topic
                    if topic not in results:
                        results[topic] = []

                    for record in records:
                        results[topic].append(record.value)
                        messages_consumed += 1

                        if messages_consumed >= max_messages:
                            break

        except KafkaError as e:
            logger.error(f"Kafka error during batch consume: {e}")

        return results

    def close(self):
        """Close the consumer connection."""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
