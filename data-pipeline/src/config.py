"""Configuration settings for the data pipeline service."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service Info
    service_name: str = "data-pipeline"
    version: str = "0.1.0"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://embeddings:embeddings_pass@localhost:5432/embeddings_saas"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_interactions: str = "interactions-raw"
    kafka_topic_items: str = "items-catalog"
    kafka_topic_features: str = "features-processed"
    kafka_topic_training: str = "training-data"

    # MinIO/S3
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_raw: str = "raw-data"
    s3_bucket_processed: str = "processed-data"
    s3_bucket_training: str = "training-data"
    s3_bucket_features: str = "features"

    # Data Processing
    negative_sampling_ratio: int = 4
    max_interactions_per_user: int = 50
    min_interactions_per_user: int = 5
    min_interactions_per_item: int = 5

    # File Upload Limits
    max_upload_size_mb: int = 500

    # PySpark
    spark_master: str = "local[*]"
    spark_app_name: str = "data-pipeline"

    # Great Expectations
    ge_context_root_dir: str = "./ge_context"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
