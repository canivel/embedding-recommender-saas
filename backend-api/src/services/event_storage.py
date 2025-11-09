"""
Event storage service for managing Parquet files and DuckDB queries.

This module handles:
- Storing event data as Parquet files
- Querying events using DuckDB
- Session detection and management
- Event statistics aggregation
"""

import os
import io
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID
import tempfile

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from src.core.config import settings

logger = structlog.get_logger()


class EventStorageService:
    """Service for storing and querying event data."""

    def __init__(self):
        """Initialize event storage service."""
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_dataset_path(self, tenant_id: UUID, dataset_id: UUID) -> Path:
        """Get storage path for a dataset."""
        path = self.storage_path / str(tenant_id) / str(dataset_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_upload_path(self, tenant_id: UUID, dataset_id: UUID, upload_id: UUID) -> Path:
        """Get storage path for an upload."""
        dataset_path = self._get_dataset_path(tenant_id, dataset_id)
        return dataset_path / f"{upload_id}.parquet"

    async def store_events(
        self,
        tenant_id: UUID,
        dataset_id: UUID,
        upload_id: UUID,
        csv_content: bytes,
        column_mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Store events from CSV to Parquet format.

        Args:
            tenant_id: Tenant UUID
            dataset_id: Dataset UUID
            upload_id: Upload UUID
            csv_content: CSV file content
            column_mapping: Column mapping configuration

        Returns:
            Dictionary with upload statistics
        """
        try:
            # Parse CSV
            decoded = csv_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(decoded))

            # Validate required columns exist
            required_cols = [
                column_mapping['user_column'],
                column_mapping['item_column'],
                column_mapping['timestamp_column'],
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Rename columns to standard names
            rename_map = {
                column_mapping['user_column']: 'user_id',
                column_mapping['item_column']: 'item_id',
                column_mapping['timestamp_column']: 'timestamp',
            }

            if column_mapping.get('session_column'):
                rename_map[column_mapping['session_column']] = 'session_id'

            if column_mapping.get('target_column'):
                rename_map[column_mapping['target_column']] = 'target'

            df = df.rename(columns=rename_map)

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Sort by user and timestamp
            df = df.sort_values(['user_id', 'timestamp'])

            # Add metadata columns
            df['tenant_id'] = str(tenant_id)
            df['dataset_id'] = str(dataset_id)
            df['upload_id'] = str(upload_id)
            df['processed_at'] = datetime.utcnow()

            # Store as Parquet
            parquet_path = self._get_upload_path(tenant_id, dataset_id, upload_id)

            table = pa.Table.from_pandas(df)
            pq.write_table(table, parquet_path, compression='snappy')

            # Calculate statistics
            stats = {
                'total_events': len(df),
                'unique_users': df['user_id'].nunique(),
                'unique_items': df['item_id'].nunique(),
                'date_range': {
                    'start': df['timestamp'].min().isoformat(),
                    'end': df['timestamp'].max().isoformat(),
                },
                'file_size_bytes': parquet_path.stat().st_size,
            }

            logger.info(
                "events_stored",
                tenant_id=str(tenant_id),
                dataset_id=str(dataset_id),
                upload_id=str(upload_id),
                total_events=stats['total_events'],
            )

            return stats

        except Exception as e:
            logger.error(
                "event_storage_failed",
                tenant_id=str(tenant_id),
                dataset_id=str(dataset_id),
                upload_id=str(upload_id),
                error=str(e),
            )
            raise

    async def detect_sessions(
        self,
        tenant_id: UUID,
        dataset_id: UUID,
        upload_id: UUID,
        timeout_minutes: int = 30,
    ) -> int:
        """
        Detect sessions in uploaded events.

        Args:
            tenant_id: Tenant UUID
            dataset_id: Dataset UUID
            upload_id: Upload UUID
            timeout_minutes: Session timeout in minutes

        Returns:
            Number of sessions detected
        """
        parquet_path = self._get_upload_path(tenant_id, dataset_id, upload_id)

        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

        # Use DuckDB for session detection
        conn = duckdb.connect(':memory:')

        query = f"""
        WITH ordered_events AS (
            SELECT
                user_id,
                item_id,
                timestamp,
                LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp) as prev_timestamp
            FROM read_parquet('{parquet_path}')
        ),
        session_breaks AS (
            SELECT
                *,
                CASE
                    WHEN prev_timestamp IS NULL THEN 1
                    WHEN EPOCH(timestamp - prev_timestamp) / 60 > {timeout_minutes} THEN 1
                    ELSE 0
                END as is_new_session
            FROM ordered_events
        ),
        sessions AS (
            SELECT
                user_id,
                item_id,
                timestamp,
                SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY timestamp) as session_number
            FROM session_breaks
        )
        SELECT
            user_id,
            session_number,
            MIN(timestamp) as session_start,
            MAX(timestamp) as session_end,
            COUNT(*) as event_count,
            ARRAY_AGG(item_id ORDER BY timestamp) as item_sequence
        FROM sessions
        GROUP BY user_id, session_number
        ORDER BY user_id, session_number
        """

        result = conn.execute(query).fetchdf()

        # Store sessions to separate parquet file
        sessions_path = self._get_upload_path(tenant_id, dataset_id, upload_id).with_suffix('.sessions.parquet')

        # Add session_id
        result['session_id'] = result['user_id'] + '_' + result['session_number'].astype(str)
        result['tenant_id'] = str(tenant_id)
        result['dataset_id'] = str(dataset_id)
        result['upload_id'] = str(upload_id)

        table = pa.Table.from_pandas(result)
        pq.write_table(table, sessions_path, compression='snappy')

        conn.close()

        logger.info(
            "sessions_detected",
            tenant_id=str(tenant_id),
            dataset_id=str(dataset_id),
            upload_id=str(upload_id),
            session_count=len(result),
        )

        return len(result)

    async def query_events(
        self,
        tenant_id: UUID,
        dataset_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Query events using DuckDB.

        Args:
            tenant_id: Tenant UUID
            dataset_id: Dataset UUID
            filters: Optional filters (user_id, item_id, date_range, etc.)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Dictionary with events and metadata
        """
        dataset_path = self._get_dataset_path(tenant_id, dataset_id)
        parquet_files = list(dataset_path.glob("*.parquet"))

        if not parquet_files:
            return {'events': [], 'total': 0}

        # Build query
        files_pattern = str(dataset_path / "*.parquet")

        where_clauses = [
            f"tenant_id = '{tenant_id}'",
            f"dataset_id = '{dataset_id}'",
        ]

        if filters:
            if filters.get('user_id'):
                where_clauses.append(f"user_id = '{filters['user_id']}'")

            if filters.get('item_id'):
                where_clauses.append(f"item_id = '{filters['item_id']}'")

            if filters.get('date_from'):
                where_clauses.append(f"timestamp >= '{filters['date_from']}'")

            if filters.get('date_to'):
                where_clauses.append(f"timestamp <= '{filters['date_to']}'")

        where_sql = " AND ".join(where_clauses)

        conn = duckdb.connect(':memory:')

        # Count total
        count_query = f"""
        SELECT COUNT(*) as total
        FROM read_parquet('{files_pattern}')
        WHERE {where_sql}
        """
        total = conn.execute(count_query).fetchone()[0]

        # Get events
        query = f"""
        SELECT *
        FROM read_parquet('{files_pattern}')
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT {limit} OFFSET {offset}
        """

        result = conn.execute(query).fetchdf()
        conn.close()

        return {
            'events': result.to_dict('records'),
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    async def get_statistics(
        self,
        tenant_id: UUID,
        dataset_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for a dataset.

        Args:
            tenant_id: Tenant UUID
            dataset_id: Dataset UUID

        Returns:
            Dictionary with statistics
        """
        dataset_path = self._get_dataset_path(tenant_id, dataset_id)
        parquet_files = list(dataset_path.glob("*.parquet"))

        if not parquet_files:
            return {
                'total_events': 0,
                'unique_users': 0,
                'unique_items': 0,
                'uploads': 0,
            }

        files_pattern = str(dataset_path / "*.parquet")
        conn = duckdb.connect(':memory:')

        query = f"""
        SELECT
            COUNT(*) as total_events,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT item_id) as unique_items,
            COUNT(DISTINCT upload_id) as uploads,
            MIN(timestamp) as earliest_event,
            MAX(timestamp) as latest_event
        FROM read_parquet('{files_pattern}')
        WHERE tenant_id = '{tenant_id}' AND dataset_id = '{dataset_id}'
        """

        result = conn.execute(query).fetchone()
        conn.close()

        return {
            'total_events': result[0],
            'unique_users': result[1],
            'unique_items': result[2],
            'uploads': result[3],
            'date_range': {
                'start': result[4].isoformat() if result[4] else None,
                'end': result[5].isoformat() if result[5] else None,
            },
        }


# Global instance
event_storage = EventStorageService()
