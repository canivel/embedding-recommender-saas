"""Kafka module for event streaming."""
from .producer import KafkaProducerClient
from .consumer import KafkaConsumerClient

__all__ = ["KafkaProducerClient", "KafkaConsumerClient"]
