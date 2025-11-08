"""
Application configuration management.

This module handles all application settings using Pydantic Settings.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.

    All settings can be overridden via environment variables.
    """

    # Application
    APP_NAME: str = "Embedding Recommender API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/embedding_recommender"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        if self.REDIS_URL:
            return self.REDIS_URL

        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_KEY_LENGTH: int = 32

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT_PER_MINUTE: int = 1000
    DEFAULT_RATE_LIMIT_PER_HOUR: int = 50000
    DEFAULT_RATE_LIMIT_PER_DAY: int = 1000000

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Upstream Services
    ML_ENGINE_URL: str = "http://localhost:8001"
    DATA_PIPELINE_URL: str = "http://localhost:8002"
    ML_ENGINE_TIMEOUT: int = 10
    DATA_PIPELINE_TIMEOUT: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Metrics
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Observability
    JAEGER_ENABLED: bool = False
    JAEGER_ENDPOINT: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
