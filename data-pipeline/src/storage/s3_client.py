"""MinIO/S3 client for object storage operations."""
import io
import logging
from typing import Optional, BinaryIO
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import pandas as pd

from ..config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """Client for interacting with MinIO/S3 storage."""

    def __init__(self):
        """Initialize S3 client with configuration."""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Ensure all required buckets exist."""
        buckets = [
            settings.s3_bucket_raw,
            settings.s3_bucket_processed,
            settings.s3_bucket_training,
            settings.s3_bucket_features,
        ]

        existing_buckets = [b['Name'] for b in self.client.list_buckets()['Buckets']]

        for bucket in buckets:
            if bucket not in existing_buckets:
                try:
                    self.client.create_bucket(Bucket=bucket)
                    logger.info(f"Created bucket: {bucket}")
                except ClientError as e:
                    logger.error(f"Failed to create bucket {bucket}: {e}")

    def upload_file(
        self,
        file_obj: BinaryIO,
        bucket: str,
        key: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to S3.

        Args:
            file_obj: File-like object to upload
            bucket: Bucket name
            key: Object key (path)
            content_type: MIME type of the file

        Returns:
            True if successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            self.client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra_args)
            logger.info(f"Uploaded file to s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file to s3://{bucket}/{key}: {e}")
            return False

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        bucket: str,
        key: str,
        format: str = "parquet"
    ) -> bool:
        """
        Upload a pandas DataFrame to S3.

        Args:
            df: DataFrame to upload
            bucket: Bucket name
            key: Object key (path)
            format: File format (parquet, csv)

        Returns:
            True if successful, False otherwise
        """
        try:
            buffer = io.BytesIO()

            if format == "parquet":
                df.to_parquet(buffer, index=False, engine='pyarrow')
                content_type = "application/octet-stream"
            elif format == "csv":
                df.to_csv(buffer, index=False)
                content_type = "text/csv"
            else:
                raise ValueError(f"Unsupported format: {format}")

            buffer.seek(0)
            return self.upload_file(buffer, bucket, key, content_type)
        except Exception as e:
            logger.error(f"Failed to upload DataFrame to s3://{bucket}/{key}: {e}")
            return False

    def download_file(self, bucket: str, key: str) -> Optional[bytes]:
        """
        Download a file from S3.

        Args:
            bucket: Bucket name
            key: Object key (path)

        Returns:
            File contents as bytes, or None if failed
        """
        try:
            buffer = io.BytesIO()
            self.client.download_fileobj(bucket, key, buffer)
            buffer.seek(0)
            return buffer.read()
        except ClientError as e:
            logger.error(f"Failed to download file from s3://{bucket}/{key}: {e}")
            return None

    def download_dataframe(
        self,
        bucket: str,
        key: str,
        format: str = "parquet"
    ) -> Optional[pd.DataFrame]:
        """
        Download a file from S3 as a pandas DataFrame.

        Args:
            bucket: Bucket name
            key: Object key (path)
            format: File format (parquet, csv)

        Returns:
            DataFrame or None if failed
        """
        try:
            buffer = io.BytesIO()
            self.client.download_fileobj(bucket, key, buffer)
            buffer.seek(0)

            if format == "parquet":
                return pd.read_parquet(buffer, engine='pyarrow')
            elif format == "csv":
                return pd.read_csv(buffer)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Failed to download DataFrame from s3://{bucket}/{key}: {e}")
            return None

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """
        List objects in a bucket with optional prefix.

        Args:
            bucket: Bucket name
            prefix: Object key prefix

        Returns:
            List of object keys
        """
        try:
            response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            logger.error(f"Failed to list objects in s3://{bucket}/{prefix}: {e}")
            return []

    def delete_object(self, bucket: str, key: str) -> bool:
        """
        Delete an object from S3.

        Args:
            bucket: Bucket name
            key: Object key (path)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted object s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object s3://{bucket}/{key}: {e}")
            return False

    def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if an object exists in S3.

        Args:
            bucket: Bucket name
            key: Object key (path)

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False


# Global instance
s3_client = S3Client()
