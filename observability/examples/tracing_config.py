"""
Distributed Tracing Configuration with Jaeger and OpenTelemetry

This module provides comprehensive distributed tracing setup for:
- Request tracing across microservices
- Database query tracing
- External API call tracing
- Custom span creation for critical operations
- Integration with FastAPI, Redis, PostgreSQL, and Kafka

Usage:
    from tracing_config import setup_tracing, trace_function, get_tracer

    # Initialize tracing on app startup
    setup_tracing(service_name="backend-api")

    # Use decorator for automatic tracing
    @trace_function(operation_name="recommend_items")
    def recommend_items(user_id: str, count: int):
        # Your code here
        pass

    # Or use tracer directly
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("custom_operation") as span:
        span.set_attribute("user_id", user_id)
        # Your code here
"""

import os
import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


# Global tracer provider
_tracer_provider: Optional[TracerProvider] = None
_propagator = TraceContextTextMapPropagator()


def setup_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    jaeger_host: str = None,
    jaeger_port: int = None,
    environment: str = None,
    sample_rate: float = 1.0
) -> TracerProvider:
    """
    Initialize OpenTelemetry tracing with Jaeger exporter.

    Args:
        service_name: Name of the service (e.g., "backend-api", "ml-engine")
        service_version: Version of the service
        jaeger_host: Jaeger agent hostname (default: from env or "localhost")
        jaeger_port: Jaeger agent port (default: from env or 6831)
        environment: Deployment environment (dev, staging, prod)
        sample_rate: Trace sampling rate (0.0 to 1.0)

    Returns:
        Configured TracerProvider instance
    """
    global _tracer_provider

    # Get Jaeger configuration from environment or use defaults
    jaeger_host = jaeger_host or os.getenv("JAEGER_AGENT_HOST", "localhost")
    jaeger_port = jaeger_port or int(os.getenv("JAEGER_AGENT_PORT", "6831"))
    environment = environment or os.getenv("ENVIRONMENT", "development")

    # Create resource with service information
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "environment": environment,
        "deployment.type": "docker" if os.getenv("DOCKER_CONTAINER") else "local"
    })

    # Configure tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )

    # Add span processor with batching for performance
    span_processor = BatchSpanProcessor(jaeger_exporter)
    _tracer_provider.add_span_processor(span_processor)

    # Set the global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Auto-instrument common libraries
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()

    try:
        Psycopg2Instrumentor().instrument()
    except Exception:
        # Psycopg2 might not be installed in all services
        pass

    print(f"Tracing initialized for {service_name} -> Jaeger at {jaeger_host}:{jaeger_port}")

    return _tracer_provider


def instrument_fastapi(app) -> None:
    """
    Instrument a FastAPI application with automatic tracing.

    Args:
        app: FastAPI application instance

    Usage:
        from fastapi import FastAPI
        from tracing_config import setup_tracing, instrument_fastapi

        app = FastAPI()
        setup_tracing(service_name="backend-api")
        instrument_fastapi(app)
    """
    FastAPIInstrumentor.instrument_app(app)
    print(f"FastAPI instrumented with OpenTelemetry tracing")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (typically __name__ or module path)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def trace_function(
    operation_name: Optional[str] = None,
    attributes: Optional[dict] = None
) -> Callable:
    """
    Decorator to automatically trace a function.

    Args:
        operation_name: Name of the operation (defaults to function name)
        attributes: Additional attributes to add to the span

    Usage:
        @trace_function(operation_name="generate_embeddings", attributes={"model": "bert"})
        def generate_embeddings(text: str) -> list:
            # Your code here
            return embeddings
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function arguments as attributes (be careful with sensitive data)
                span.set_attribute("function.name", func.__name__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer(func.__module__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                span.set_attribute("function.name", func.__name__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def trace_span(
    operation_name: str,
    attributes: Optional[dict] = None,
    tracer_name: Optional[str] = None
):
    """
    Context manager for creating custom spans.

    Args:
        operation_name: Name of the operation
        attributes: Attributes to add to the span
        tracer_name: Name of the tracer (defaults to __name__)

    Usage:
        with trace_span("database_query", {"query_type": "SELECT"}):
            result = db.execute(query)
    """
    tracer = get_tracer(tracer_name or __name__)

    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def inject_trace_context(headers: dict) -> dict:
    """
    Inject trace context into HTTP headers for propagation.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        Headers with trace context injected

    Usage:
        headers = {"Authorization": "Bearer token"}
        headers = inject_trace_context(headers)
        response = requests.get(url, headers=headers)
    """
    _propagator.inject(headers)
    return headers


def extract_trace_context(headers: dict) -> trace.SpanContext:
    """
    Extract trace context from HTTP headers.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        Extracted span context

    Usage:
        context = extract_trace_context(request.headers)
    """
    return _propagator.extract(headers)


# Example instrumentation for specific operations
class DatabaseTracer:
    """Helper class for tracing database operations."""

    @staticmethod
    @contextmanager
    def trace_query(query: str, operation: str = "query"):
        """
        Trace a database query.

        Usage:
            with DatabaseTracer.trace_query("SELECT * FROM users WHERE id = ?"):
                result = db.execute(query, params)
        """
        tracer = get_tracer("database")
        with tracer.start_as_current_span(f"db.{operation}") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


class MLTracer:
    """Helper class for tracing ML operations."""

    @staticmethod
    @contextmanager
    def trace_inference(model_name: str, model_version: str = "latest"):
        """
        Trace ML model inference.

        Usage:
            with MLTracer.trace_inference("bert-base", "v1.0"):
                embeddings = model.encode(text)
        """
        tracer = get_tracer("ml")
        with tracer.start_as_current_span("ml.inference") as span:
            span.set_attribute("ml.model.name", model_name)
            span.set_attribute("ml.model.version", model_version)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @staticmethod
    @contextmanager
    def trace_training(model_name: str, dataset_size: int):
        """
        Trace ML model training.

        Usage:
            with MLTracer.trace_training("collaborative-filter", 10000):
                model.fit(X_train, y_train)
        """
        tracer = get_tracer("ml")
        with tracer.start_as_current_span("ml.training") as span:
            span.set_attribute("ml.model.name", model_name)
            span.set_attribute("ml.dataset.size", dataset_size)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


class CacheTracer:
    """Helper class for tracing cache operations."""

    @staticmethod
    @contextmanager
    def trace_operation(operation: str, key: str):
        """
        Trace cache operation (get, set, delete).

        Usage:
            with CacheTracer.trace_operation("get", "user:123"):
                value = redis.get(key)
        """
        tracer = get_tracer("cache")
        with tracer.start_as_current_span(f"cache.{operation}") as span:
            span.set_attribute("cache.operation", operation)
            span.set_attribute("cache.key", key)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# Example usage
if __name__ == "__main__":
    import time

    # Setup tracing
    setup_tracing(
        service_name="example-service",
        service_version="1.0.0",
        environment="development"
    )

    # Example 1: Using decorator
    @trace_function(operation_name="process_user_request")
    def process_request(user_id: str):
        time.sleep(0.1)
        print(f"Processing request for user {user_id}")
        return {"status": "success"}

    # Example 2: Using context manager
    def fetch_recommendations(user_id: str):
        with trace_span("fetch_recommendations", {"user_id": user_id}):
            time.sleep(0.05)

            # Nested span for database query
            with DatabaseTracer.trace_query("SELECT * FROM items WHERE user_id = ?"):
                time.sleep(0.02)

            # Nested span for ML inference
            with MLTracer.trace_inference("recommendation-model", "v2.0"):
                time.sleep(0.03)

            return ["item1", "item2", "item3"]

    # Run examples
    process_request("user-123")
    fetch_recommendations("user-456")

    print("Tracing examples completed. View traces at http://localhost:16686")
