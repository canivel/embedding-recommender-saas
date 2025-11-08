"""Data quality checks and monitoring."""
import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """Check data quality metrics."""

    def check_interactions_quality(
        self,
        interactions_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Check quality metrics for interaction data.

        Args:
            interactions_df: Interaction DataFrame

        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            'total_rows': len(interactions_df),
            'unique_users': interactions_df['user_id'].nunique(),
            'unique_items': interactions_df['item_id'].nunique(),
            'interaction_types': interactions_df['interaction_type'].value_counts().to_dict(),
            'null_counts': interactions_df.isnull().sum().to_dict(),
            'duplicate_rows': interactions_df.duplicated().sum(),
        }

        # Check for users/items with very few interactions
        user_counts = interactions_df['user_id'].value_counts()
        item_counts = interactions_df['item_id'].value_counts()

        metrics['users_with_few_interactions'] = (user_counts < 5).sum()
        metrics['items_with_few_interactions'] = (item_counts < 5).sum()

        # Timestamp range
        if 'timestamp' in interactions_df.columns:
            interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])
            metrics['timestamp_range'] = {
                'min': interactions_df['timestamp'].min().isoformat(),
                'max': interactions_df['timestamp'].max().isoformat(),
            }

        logger.info(f"Quality metrics: {metrics}")

        return metrics

    def check_items_quality(
        self,
        items_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Check quality metrics for item data.

        Args:
            items_df: Items DataFrame

        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            'total_items': len(items_df),
            'unique_items': items_df['item_id'].nunique(),
            'duplicate_items': items_df['item_id'].duplicated().sum(),
            'null_counts': items_df.isnull().sum().to_dict(),
        }

        if 'category' in items_df.columns:
            metrics['categories'] = items_df['category'].value_counts().to_dict()

        logger.info(f"Item quality metrics: {metrics}")

        return metrics
