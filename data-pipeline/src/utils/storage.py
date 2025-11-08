"""
S3-compatible storage client (MinIO/AWS S3)
Handles reading and writing data to object storage
"""
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import io
import logging
from typing import Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class S3StorageClient:
    """S3-compatible storage client for data operations"""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: str = "embeddings-data"
    ):
        """
        Initialize S3 client

        Args:
            endpoint_url: S3 endpoint (None for AWS, URL for MinIO)
            access_key: Access key
            secret_key: Secret key
            bucket_name: Default bucket name
        """
        # Get credentials from environment if not provided
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL")
        self.access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
        self.secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
        self.bucket_name = bucket_name

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=os.getenv("AWS_REGION", "us-west-2")
        )

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Error creating bucket: {e}")

    def write_parquet(
        self,
        df: pd.DataFrame,
        s3_path: str,
        tenant_id: str,
        data_type: str
    ) -> bool:
        """
        Write DataFrame to S3 as Parquet

        Args:
            df: DataFrame to write
            s3_path: Full S3 path (s3://bucket/key)
            tenant_id: Tenant identifier
            data_type: Type of data

        Returns:
            True if successful
        """
        try:
            # Parse S3 path
            path_parts = s3_path.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key = path_parts[1] if len(path_parts) > 1 else ""

            # Convert DataFrame to Parquet in memory
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, engine='pyarrow')
            buffer.seek(0)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=buffer.getvalue(),
                Metadata={
                    'tenant_id': tenant_id,
                    'data_type': data_type,
                    'row_count': str(len(df))
                }
            )

            logger.info(f"Successfully wrote {len(df)} rows to {s3_path}")
            return True

        except Exception as e:
            logger.error(f"Error writing to S3: {e}", exc_info=True)
            return False

    def read_parquet(self, s3_path: str) -> pd.DataFrame:
        """
        Read Parquet file from S3

        Args:
            s3_path: Full S3 path (s3://bucket/key)

        Returns:
            DataFrame
        """
        try:
            # Parse S3 path
            path_parts = s3_path.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key = path_parts[1] if len(path_parts) > 1 else ""

            # Download from S3
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            buffer = io.BytesIO(response['Body'].read())

            # Read Parquet
            df = pd.read_parquet(buffer, engine='pyarrow')

            logger.info(f"Successfully read {len(df)} rows from {s3_path}")
            return df

        except Exception as e:
            logger.error(f"Error reading from S3: {e}", exc_info=True)
            raise

    def list_objects(self, prefix: str, bucket: Optional[str] = None) -> list:
        """
        List objects in S3 with given prefix

        Args:
            prefix: S3 key prefix
            bucket: Bucket name (uses default if None)

        Returns:
            List of object keys
        """
        try:
            bucket = bucket or self.bucket_name
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )

            objects = []
            if 'Contents' in response:
                objects = [obj['Key'] for obj in response['Contents']]

            return objects

        except Exception as e:
            logger.error(f"Error listing objects: {e}", exc_info=True)
            return []

    def delete_object(self, key: str, bucket: Optional[str] = None) -> bool:
        """
        Delete object from S3

        Args:
            key: S3 object key
            bucket: Bucket name (uses default if None)

        Returns:
            True if successful
        """
        try:
            bucket = bucket or self.bucket_name
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted object: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting object: {e}", exc_info=True)
            return False

    def delete_user_data(self, tenant_id: str, user_id: str) -> int:
        """
        Delete all data for a specific user (GDPR compliance)

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            Number of files processed
        """
        try:
            files_processed = 0

            # List all interaction files for tenant
            prefix = f"{tenant_id}/raw/interactions/"
            objects = self.list_objects(prefix)

            for obj_key in objects:
                # Read, filter, and rewrite
                s3_path = f"s3://{self.bucket_name}/{obj_key}"
                df = self.read_parquet(s3_path)

                original_count = len(df)
                df_filtered = df[df['user_id'] != user_id]
                filtered_count = len(df_filtered)

                if original_count != filtered_count:
                    # Data was removed, rewrite file
                    if len(df_filtered) > 0:
                        self.write_parquet(df_filtered, s3_path, tenant_id, "interactions")
                    else:
                        # File is empty, delete it
                        self.delete_object(obj_key)

                    logger.info(f"Removed {original_count - filtered_count} rows for user {user_id} from {obj_key}")
                    files_processed += 1

            return files_processed

        except Exception as e:
            logger.error(f"Error deleting user data: {e}", exc_info=True)
            raise

    def export_user_data(self, tenant_id: str, user_id: str) -> pd.DataFrame:
        """
        Export all data for a specific user (GDPR compliance)

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            DataFrame with all user data
        """
        try:
            all_data = []

            # List all interaction files for tenant
            prefix = f"{tenant_id}/raw/interactions/"
            objects = self.list_objects(prefix)

            for obj_key in objects:
                s3_path = f"s3://{self.bucket_name}/{obj_key}"
                df = self.read_parquet(s3_path)
                user_data = df[df['user_id'] == user_id]

                if len(user_data) > 0:
                    all_data.append(user_data)

            if all_data:
                result = pd.concat(all_data, ignore_index=True)
                logger.info(f"Exported {len(result)} rows for user {user_id}")
                return result
            else:
                logger.info(f"No data found for user {user_id}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error exporting user data: {e}", exc_info=True)
            raise
