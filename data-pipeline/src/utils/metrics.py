"""
Prometheus metrics for data ingestion pipeline
Tracks data quality and ingestion performance
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import logging

logger = logging.getLogger(__name__)


class DataIngestionMetrics:
    """Prometheus metrics for data ingestion"""

    def __init__(self):
        # Upload metrics
        self.upload_total = Counter(
            'data_ingestion_uploads_total',
            'Total number of data uploads',
            ['tenant_id', 'data_type', 'status']
        )

        self.upload_rows = Counter(
            'data_ingestion_rows_total',
            'Total number of rows ingested',
            ['tenant_id', 'data_type']
        )

        self.upload_duration = Histogram(
            'data_ingestion_upload_duration_seconds',
            'Time taken to process uploads',
            ['tenant_id', 'data_type']
        )

        # Validation metrics
        self.validation_errors = Counter(
            'data_ingestion_validation_errors_total',
            'Total number of validation errors',
            ['tenant_id', 'data_type', 'error_type']
        )

        # Data quality metrics
        self.data_freshness = Gauge(
            'data_ingestion_freshness_hours',
            'Hours since last data ingestion',
            ['tenant_id', 'data_type']
        )

        self.data_completeness = Gauge(
            'data_ingestion_completeness_percent',
            'Percentage of complete records',
            ['tenant_id', 'data_type']
        )

        self.data_validity = Gauge(
            'data_ingestion_validity_percent',
            'Percentage of valid records',
            ['tenant_id', 'data_type']
        )

        # Processing metrics
        self.processing_duration = Histogram(
            'data_ingestion_processing_duration_seconds',
            'Time taken to process data',
            ['tenant_id', 'job_type']
        )

        self.processing_errors = Counter(
            'data_ingestion_processing_errors_total',
            'Total number of processing errors',
            ['tenant_id', 'job_type', 'error_type']
        )

    def record_upload(
        self,
        tenant_id: str,
        data_type: str,
        rows_accepted: int,
        rows_rejected: int,
        duration: float
    ):
        """Record upload metrics"""
        status = 'success' if rows_rejected == 0 else 'partial'
        self.upload_total.labels(tenant_id=tenant_id, data_type=data_type, status=status).inc()
        self.upload_rows.labels(tenant_id=tenant_id, data_type=data_type).inc(rows_accepted)
        self.upload_duration.labels(tenant_id=tenant_id, data_type=data_type).observe(duration)

        logger.info(f"Recorded upload metrics: {tenant_id}/{data_type} - {rows_accepted} rows in {duration:.2f}s")

    def record_upload_error(self, tenant_id: str, data_type: str, error_message: str):
        """Record upload error"""
        self.upload_total.labels(tenant_id=tenant_id, data_type=data_type, status='error').inc()
        logger.error(f"Upload error: {tenant_id}/{data_type} - {error_message}")

    def record_validation_error(
        self,
        tenant_id: str,
        data_type: str,
        error_type: str
    ):
        """Record validation error"""
        self.validation_errors.labels(
            tenant_id=tenant_id,
            data_type=data_type,
            error_type=error_type
        ).inc()

    def update_data_quality(
        self,
        tenant_id: str,
        data_type: str,
        freshness_hours: float,
        completeness_percent: float,
        validity_percent: float
    ):
        """Update data quality metrics"""
        self.data_freshness.labels(tenant_id=tenant_id, data_type=data_type).set(freshness_hours)
        self.data_completeness.labels(tenant_id=tenant_id, data_type=data_type).set(completeness_percent)
        self.data_validity.labels(tenant_id=tenant_id, data_type=data_type).set(validity_percent)

    def record_processing(
        self,
        tenant_id: str,
        job_type: str,
        duration: float
    ):
        """Record processing job metrics"""
        self.processing_duration.labels(tenant_id=tenant_id, job_type=job_type).observe(duration)

    def record_processing_error(
        self,
        tenant_id: str,
        job_type: str,
        error_type: str
    ):
        """Record processing error"""
        self.processing_errors.labels(
            tenant_id=tenant_id,
            job_type=job_type,
            error_type=error_type
        ).inc()


# Global metrics instance
metrics = DataIngestionMetrics()
