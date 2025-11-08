"""
Structured JSON Logging Configuration for Embedding Recommender SaaS

This module provides a comprehensive logging setup with:
- Structured JSON output for Loki ingestion
- Contextual logging with tenant/user/request tracking
- Performance metrics logging
- Error tracking with stack traces
- Integration with Python logging and third-party libraries

Usage:
    from logging_config import setup_logging, get_logger

    setup_logging(service_name="backend-api", log_level="INFO")
    logger = get_logger(__name__)

    logger.info("Processing request", extra={
        "tenant_id": "tenant-123",
        "user_id": "user-456",
        "endpoint": "/recommendations"
    })
"""

import logging
import logging.config
import sys
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
import contextvars

# Context variables for request tracking
request_id_ctx = contextvars.ContextVar("request_id", default=None)
tenant_id_ctx = contextvars.ContextVar("tenant_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging compatible with Loki.

    Outputs logs in JSON format with consistent fields:
    - timestamp: ISO 8601 format
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - service: Service name
    - Additional context fields
    """

    def __init__(self, service_name: str = "unknown-service"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context variables if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        tenant_id = tenant_id_ctx.get()
        if tenant_id:
            log_data["tenant_id"] = tenant_id

        user_id = user_id_ctx.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add extra fields from log record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info)
            }

        # Add extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "extra_fields"
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ContextFilter(logging.Filter):
    """Filter to inject context variables into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context variables to the log record."""
        record.request_id = request_id_ctx.get()
        record.tenant_id = tenant_id_ctx.get()
        record.user_id = user_id_ctx.get()
        return True


def setup_logging(
    service_name: str = "unknown-service",
    log_level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[str] = None
) -> None:
    """
    Configure logging with JSON formatting for the service.

    Args:
        service_name: Name of the service (e.g., "backend-api", "ml-engine")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to also log to a file
        log_file_path: Path to log file (if log_to_file is True)
    """
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
            "filters": ["context"]
        }
    }

    if log_to_file and log_file_path:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": log_file_path,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "filters": ["context"]
        }

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
                "service_name": service_name
            }
        },
        "filters": {
            "context": {
                "()": ContextFilter
            }
        },
        "handlers": handlers,
        "root": {
            "level": log_level,
            "handlers": list(handlers.keys())
        },
        "loggers": {
            # Quiet down noisy libraries
            "urllib3": {"level": "WARNING"},
            "botocore": {"level": "WARNING"},
            "kafka": {"level": "WARNING"},
            "aiokafka": {"level": "WARNING"},
        }
    }

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_request_context(
    request_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Set context variables for the current request.

    Args:
        request_id: Unique request identifier
        tenant_id: Tenant identifier
        user_id: User identifier
    """
    if request_id:
        request_id_ctx.set(request_id)
    if tenant_id:
        tenant_id_ctx.set(tenant_id)
    if user_id:
        user_id_ctx.set(user_id)


def clear_request_context() -> None:
    """Clear all request context variables."""
    request_id_ctx.set(None)
    tenant_id_ctx.set(None)
    user_id_ctx.set(None)


# FastAPI integration
class LoggingMiddleware:
    """
    FastAPI middleware for automatic request logging and context injection.

    Usage:
        from fastapi import FastAPI
        from logging_config import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
    """

    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Generate request ID if not present
        request_id = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-request-id":
                request_id = header_value.decode()
                break

        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())

        # Set context
        set_request_context(request_id=request_id)

        # Log request
        self.logger.info(
            f"{scope['method']} {scope['path']}",
            extra={
                "event": "request_started",
                "method": scope["method"],
                "path": scope["path"],
                "query_string": scope.get("query_string", b"").decode()
            }
        )

        try:
            await self.app(scope, receive, send)
        except Exception as e:
            self.logger.error(
                f"Request failed: {str(e)}",
                exc_info=True,
                extra={
                    "event": "request_failed",
                    "method": scope["method"],
                    "path": scope["path"]
                }
            )
            raise
        finally:
            clear_request_context()


# Example usage
if __name__ == "__main__":
    # Setup logging
    setup_logging(service_name="example-service", log_level="DEBUG")
    logger = get_logger(__name__)

    # Basic logging
    logger.info("Service started")
    logger.debug("Debug information", extra={"config": {"port": 8000}})

    # Logging with context
    set_request_context(
        request_id="req-123",
        tenant_id="tenant-abc",
        user_id="user-456"
    )

    logger.info("Processing recommendation request", extra={
        "item_count": 100,
        "algorithm": "collaborative-filtering"
    })

    # Error logging
    try:
        raise ValueError("Example error")
    except Exception as e:
        logger.error("Failed to process request", exc_info=True, extra={
            "error_code": "PROC_ERR_001"
        })

    clear_request_context()

    # Performance logging
    import time
    start = time.time()
    time.sleep(0.1)
    duration = time.time() - start

    logger.info("Operation completed", extra={
        "event": "operation_completed",
        "operation": "model_inference",
        "duration_seconds": duration,
        "success": True
    })
