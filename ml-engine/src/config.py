"""Configuration management for ML Engine."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Service Configuration
    service_name: str = "ml-engine"
    service_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8001
    LOG_LEVEL: str = "INFO"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_embedding_ttl: int = 3600  # 1 hour for user embeddings
    redis_item_ttl: int = 86400  # 24 hours for item embeddings

    # S3/MinIO Configuration
    s3_endpoint_url: Optional[str] = None  # None for AWS S3, set for MinIO
    s3_bucket: str = "embeddings-training-data"
    s3_region: str = "us-west-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # Model Configuration
    embedding_dim: int = 64
    num_layers: int = 3
    batch_size: int = 1024
    learning_rate: float = 0.001
    num_epochs: int = 20

    # Training Configuration
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    negative_sampling_ratio: int = 4  # negatives per positive

    # FAISS Configuration
    faiss_index_type: str = "IVF"  # "IVF" or "Flat"
    faiss_nlist: int = 100  # number of clusters for IVF
    faiss_m: int = 8  # number of subquantizers
    faiss_nbits: int = 8  # bits per subquantizer

    # Serving Configuration
    recommendation_count: int = 10
    max_recommendation_count: int = 100
    cold_start_popular_count: int = 50

    # Performance Configuration
    num_workers: int = 4
    device: str = "cpu"  # "cpu" or "cuda"

    # Metrics
    target_ndcg_10: float = 0.35
    target_latency_ms: float = 50.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
