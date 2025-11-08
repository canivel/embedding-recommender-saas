"""
ML Engine Instrumentation Example
This example shows how to instrument the ML recommendation engine with:
- Training job metrics
- Model performance metrics
- Inference latency tracking
- Data pipeline metrics
- Cache efficiency metrics
"""

import time
import logging
import json
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# ============================================================================
# PROMETHEUS METRICS FOR ML ENGINE
# ============================================================================

registry = CollectorRegistry()

# Training metrics
training_job_total = Counter(
    'training_job_total',
    'Total training jobs initiated',
    ['tenant_id', 'model_type'],
    registry=registry
)

training_job_duration_seconds = Histogram(
    'training_job_duration_seconds',
    'Training job duration in seconds',
    ['tenant_id', 'model_type'],
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400),
    registry=registry
)

training_job_failures_total = Counter(
    'training_job_failures_total',
    'Total training job failures',
    ['tenant_id', 'model_type', 'error_type'],
    registry=registry
)

training_job_status = Gauge(
    'training_job_status',
    'Training job status (0=failed, 1=running, 2=completed)',
    ['tenant_id', 'job_id', 'model_type'],
    registry=registry
)

# Model performance metrics
ml_recommendation_quality = Gauge(
    'ml_recommendation_quality',
    'Recommendation quality metrics',
    ['tenant_id', 'metric', 'model_version'],
    registry=registry
)

ml_model_inference_duration_seconds = Histogram(
    'ml_model_inference_duration_seconds',
    'Model inference duration',
    ['tenant_id', 'model_type', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5),
    registry=registry
)

ml_data_pipeline_duration_seconds = Histogram(
    'ml_data_pipeline_duration_seconds',
    'Data pipeline stage duration',
    ['tenant_id', 'stage'],
    buckets=(1, 10, 60, 300, 1800),
    registry=registry
)

# Embedding and ANN metrics
embedding_cache_size_bytes = Gauge(
    'embedding_cache_size_bytes',
    'Embedding cache size in bytes',
    ['tenant_id'],
    registry=registry
)

embedding_cache_hit_ratio = Gauge(
    'embedding_cache_hit_ratio',
    'Embedding cache hit ratio',
    ['tenant_id'],
    registry=registry
)

embedding_cache_last_update_timestamp = Gauge(
    'embedding_cache_last_update_timestamp',
    'Last embedding cache update timestamp',
    ['tenant_id'],
    registry=registry
)

ann_search_duration_seconds = Histogram(
    'ann_search_duration_seconds',
    'ANN search duration',
    ['tenant_id', 'index_type'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry
)

ann_search_top_k = Histogram(
    'ann_search_top_k',
    'ANN search top-k values',
    ['tenant_id', 'index_type'],
    buckets=(1, 5, 10, 50, 100, 500),
    registry=registry
)

# Data quality metrics
data_validation_errors_total = Counter(
    'data_validation_errors_total',
    'Total data validation errors',
    ['tenant_id', 'error_type'],
    registry=registry
)

data_ingestion_records_total = Counter(
    'data_ingestion_records_total',
    'Total records ingested',
    ['tenant_id', 'data_type'],
    registry=registry
)

data_freshness_hours = Gauge(
    'data_freshness_hours',
    'Hours since last data update',
    ['tenant_id'],
    registry=registry
)


# ============================================================================
# STRUCTURED LOGGING
# ============================================================================

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# ============================================================================
# ML ENGINE CLASSES WITH INSTRUMENTATION
# ============================================================================

@dataclass
class TrainingMetrics:
    """Metrics collected during training"""
    ndcg_10: float
    ndcg_50: float
    recall_10: float
    recall_50: float
    mrr: float
    training_loss: float
    validation_loss: float


class MLEngine:
    """Example ML Engine with comprehensive instrumentation"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.cache_hits = 0
        self.cache_misses = 0
        self.embedding_cache = {}
        self.embedding_cache_update_time = time.time()

    def train_model(self, data_path: str, model_type: str = "two-tower"):
        """
        Train a recommendation model.
        Records:
        - Training duration
        - Model performance metrics
        - Data pipeline metrics
        """
        job_id = f"job_{int(time.time())}"
        training_job_total.labels(tenant_id=self.tenant_id, model_type=model_type).inc()
        training_job_status.labels(
            tenant_id=self.tenant_id,
            job_id=job_id,
            model_type=model_type
        ).set(1)  # Running

        with tracer.start_as_current_span("train_model") as span:
            span.set_attribute("tenant_id", self.tenant_id)
            span.set_attribute("model_type", model_type)
            span.set_attribute("job_id", job_id)

            start_time = time.time()

            try:
                # Data loading stage
                data_load_start = time.time()
                with tracer.start_as_current_span("data_loading"):
                    # Simulate data loading with validation
                    num_users = 10000
                    num_items = 50000
                    num_interactions = 1000000

                    data_validation_errors = self._validate_data(num_interactions)
                    for error_type, count in data_validation_errors.items():
                        data_validation_errors_total.labels(
                            tenant_id=self.tenant_id,
                            error_type=error_type
                        ).inc(count)

                    data_ingestion_records_total.labels(
                        tenant_id=self.tenant_id,
                        data_type="user_interactions"
                    ).inc(num_interactions)

                data_load_duration = time.time() - data_load_start
                ml_data_pipeline_duration_seconds.labels(
                    tenant_id=self.tenant_id,
                    stage="data_loading"
                ).observe(data_load_duration)

                logger.info(
                    f"Data loading complete for {self.tenant_id}",
                    extra={
                        "tenant_id": self.tenant_id,
                        "duration_ms": data_load_duration * 1000,
                        "num_users": num_users,
                        "num_items": num_items,
                        "num_interactions": num_interactions
                    }
                )

                # Feature engineering stage
                feature_eng_start = time.time()
                with tracer.start_as_current_span("feature_engineering"):
                    # Simulate feature engineering
                    time.sleep(0.1)

                feature_eng_duration = time.time() - feature_eng_start
                ml_data_pipeline_duration_seconds.labels(
                    tenant_id=self.tenant_id,
                    stage="feature_engineering"
                ).observe(feature_eng_duration)

                # Model training stage
                training_start = time.time()
                with tracer.start_as_current_span("model_training"):
                    # Simulate training loop
                    epochs = 10
                    for epoch in range(epochs):
                        time.sleep(0.05)  # Simulate epoch training

                training_duration = time.time() - training_start
                ml_data_pipeline_duration_seconds.labels(
                    tenant_id=self.tenant_id,
                    stage="model_training"
                ).observe(training_duration)

                # Model evaluation stage
                eval_start = time.time()
                with tracer.start_as_current_span("model_evaluation"):
                    metrics = self._evaluate_model()

                eval_duration = time.time() - eval_start
                ml_data_pipeline_duration_seconds.labels(
                    tenant_id=self.tenant_id,
                    stage="model_evaluation"
                ).observe(eval_duration)

                # Record model performance metrics
                ml_recommendation_quality.labels(
                    tenant_id=self.tenant_id,
                    metric="ndcg_10",
                    model_version="1.0"
                ).set(metrics.ndcg_10)

                ml_recommendation_quality.labels(
                    tenant_id=self.tenant_id,
                    metric="recall_10",
                    model_version="1.0"
                ).set(metrics.recall_10)

                ml_recommendation_quality.labels(
                    tenant_id=self.tenant_id,
                    metric="mrr",
                    model_version="1.0"
                ).set(metrics.mrr)

                logger.info(
                    f"Model training completed for {self.tenant_id}",
                    extra={
                        "tenant_id": self.tenant_id,
                        "job_id": job_id,
                        "total_duration_ms": (time.time() - start_time) * 1000,
                        "metrics": {
                            "ndcg_10": metrics.ndcg_10,
                            "recall_10": metrics.recall_10,
                            "mrr": metrics.mrr
                        }
                    }
                )

                # Mark as completed
                training_job_status.labels(
                    tenant_id=self.tenant_id,
                    job_id=job_id,
                    model_type=model_type
                ).set(2)  # Completed

                total_duration = time.time() - start_time
                training_job_duration_seconds.labels(
                    tenant_id=self.tenant_id,
                    model_type=model_type
                ).observe(total_duration)

                return {
                    "job_id": job_id,
                    "status": "completed",
                    "duration_seconds": total_duration,
                    "metrics": {
                        "ndcg_10": metrics.ndcg_10,
                        "recall_10": metrics.recall_10,
                        "mrr": metrics.mrr
                    }
                }

            except Exception as e:
                logger.error(
                    f"Training failed for {self.tenant_id}",
                    extra={
                        "tenant_id": self.tenant_id,
                        "error": str(e),
                        "job_id": job_id
                    }
                )
                training_job_failures_total.labels(
                    tenant_id=self.tenant_id,
                    model_type=model_type,
                    error_type=type(e).__name__
                ).inc()

                training_job_status.labels(
                    tenant_id=self.tenant_id,
                    job_id=job_id,
                    model_type=model_type
                ).set(0)  # Failed

                raise

    def get_recommendations(self, user_id: str, top_k: int = 10) -> List[Dict]:
        """
        Get recommendations for a user.
        Records:
        - Embedding lookup latency
        - Cache hit ratio
        - ANN search latency
        """
        with tracer.start_as_current_span("get_recommendations") as span:
            span.set_attribute("tenant_id", self.tenant_id)
            span.set_attribute("user_id", user_id)
            span.set_attribute("top_k", top_k)

            # Embedding lookup with cache
            with tracer.start_as_current_span("get_user_embedding"):
                embedding_start = time.time()

                if user_id in self.embedding_cache:
                    self.cache_hits += 1
                    embedding = self.embedding_cache[user_id]
                    cache_hit = True
                else:
                    self.cache_misses += 1
                    embedding = self._generate_embedding(user_id)
                    cache_hit = False

                embedding_duration = time.time() - embedding_start

                # Update cache hit ratio
                total_lookups = self.cache_hits + self.cache_misses
                hit_ratio = self.cache_hits / total_lookups if total_lookups > 0 else 0
                embedding_cache_hit_ratio.labels(tenant_id=self.tenant_id).set(hit_ratio)

                logger.debug(
                    f"Embedding lookup for user {user_id}",
                    extra={
                        "tenant_id": self.tenant_id,
                        "user_id": user_id,
                        "cache_hit": cache_hit,
                        "duration_ms": embedding_duration * 1000
                    }
                )

            # ANN search
            with tracer.start_as_current_span("ann_search"):
                ann_start = time.time()
                recommendations = self._ann_search(embedding, top_k)
                ann_duration = time.time() - ann_start

                ann_search_duration_seconds.labels(
                    tenant_id=self.tenant_id,
                    index_type="faiss"
                ).observe(ann_duration)

                ann_search_top_k.labels(
                    tenant_id=self.tenant_id,
                    index_type="faiss"
                ).observe(top_k)

                logger.debug(
                    f"ANN search completed",
                    extra={
                        "tenant_id": self.tenant_id,
                        "top_k": top_k,
                        "results": len(recommendations),
                        "duration_ms": ann_duration * 1000
                    }
                )

            return recommendations

    def _validate_data(self, num_records: int) -> Dict[str, int]:
        """Simulate data validation"""
        return {
            "duplicate_interactions": 5,
            "invalid_user_id": 2,
            "invalid_item_id": 1,
        }

    def _evaluate_model(self) -> TrainingMetrics:
        """Simulate model evaluation"""
        import random
        return TrainingMetrics(
            ndcg_10=0.35 + random.uniform(-0.05, 0.1),
            ndcg_50=0.42 + random.uniform(-0.05, 0.1),
            recall_10=0.28 + random.uniform(-0.05, 0.1),
            recall_50=0.45 + random.uniform(-0.05, 0.1),
            mrr=0.52 + random.uniform(-0.05, 0.1),
            training_loss=0.25 + random.uniform(-0.05, 0.05),
            validation_loss=0.28 + random.uniform(-0.05, 0.05),
        )

    def _generate_embedding(self, user_id: str) -> List[float]:
        """Generate user embedding (simulated)"""
        import random
        return [random.random() for _ in range(128)]

    def _ann_search(self, embedding: List[float], top_k: int) -> List[Dict]:
        """Simulate ANN search"""
        import random
        return [
            {
                "item_id": f"item_{i}",
                "score": random.uniform(0.7, 1.0),
                "similarity": "cosine"
            }
            for i in range(top_k)
        ]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Setup tracing
    jaeger_exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(trace_provider)

    # Create engine and train model
    engine = MLEngine(tenant_id="tenant_001")

    print("Starting model training...")
    result = engine.train_model(data_path="/data/tenant_001", model_type="two-tower")
    print(f"Training result: {result}")

    # Get recommendations
    print("\nGetting recommendations...")
    recs = engine.get_recommendations(user_id="user_123", top_k=10)
    print(f"Recommendations: {recs}")
