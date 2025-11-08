"""Feature engineering for user and item features."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from ..config import settings
from ..storage.s3_client import s3_client

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Feature engineering for users and items."""

    def __init__(self):
        """Initialize feature engineer."""
        self.max_interactions_per_user = settings.max_interactions_per_user

    def compute_user_features(
        self,
        interactions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute user-level features from interactions.

        Args:
            interactions_df: DataFrame with columns: user_id, item_id, interaction_type, timestamp, rating (optional)

        Returns:
            DataFrame with user features
        """
        logger.info(f"Computing user features from {len(interactions_df)} interactions")

        # Ensure timestamp is datetime
        interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])

        # Group by user
        user_stats = []

        for user_id, group in interactions_df.groupby('user_id'):
            # Basic stats
            total_interactions = len(group)
            unique_items = group['item_id'].nunique()

            # Interaction type distribution
            interaction_types = group['interaction_type'].value_counts().to_dict()

            # Rating stats (if available)
            avg_rating = None
            if 'rating' in group.columns:
                ratings = group['rating'].dropna()
                if len(ratings) > 0:
                    avg_rating = float(ratings.mean())

            # Temporal features
            last_interaction = group['timestamp'].max()
            first_interaction = group['timestamp'].min()
            days_active = (last_interaction - first_interaction).days + 1

            # Most recent N interactions
            recent_items = group.nlargest(self.max_interactions_per_user, 'timestamp')['item_id'].tolist()

            user_features = {
                'user_id': user_id,
                'total_interactions': total_interactions,
                'unique_items': unique_items,
                'avg_rating': avg_rating,
                'last_interaction': last_interaction.isoformat(),
                'first_interaction': first_interaction.isoformat(),
                'days_active': days_active,
                'interactions_per_day': total_interactions / max(days_active, 1),
                'recent_items': recent_items[:self.max_interactions_per_user],
                'num_views': interaction_types.get('view', 0),
                'num_clicks': interaction_types.get('click', 0),
                'num_purchases': interaction_types.get('purchase', 0),
                'num_likes': interaction_types.get('like', 0),
                'num_cart_adds': interaction_types.get('add_to_cart', 0),
                'conversion_rate': interaction_types.get('purchase', 0) / total_interactions if total_interactions > 0 else 0,
            }

            user_stats.append(user_features)

        user_features_df = pd.DataFrame(user_stats)

        logger.info(f"Computed features for {len(user_features_df)} users")

        return user_features_df

    def compute_item_features(
        self,
        interactions_df: pd.DataFrame,
        items_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Compute item-level features from interactions.

        Args:
            interactions_df: DataFrame with interaction data
            items_df: Optional DataFrame with item metadata

        Returns:
            DataFrame with item features
        """
        logger.info(f"Computing item features from {len(interactions_df)} interactions")

        # Ensure timestamp is datetime
        interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])

        # Group by item
        item_stats = []

        for item_id, group in interactions_df.groupby('item_id'):
            # Basic stats
            total_interactions = len(group)
            unique_users = group['user_id'].nunique()

            # Interaction type distribution
            interaction_types = group['interaction_type'].value_counts().to_dict()

            # Rating stats (if available)
            avg_rating = None
            rating_count = 0
            if 'rating' in group.columns:
                ratings = group['rating'].dropna()
                if len(ratings) > 0:
                    avg_rating = float(ratings.mean())
                    rating_count = len(ratings)

            # Temporal features
            last_interaction = group['timestamp'].max()
            first_interaction = group['timestamp'].min()

            # Popularity metrics
            popularity_score = total_interactions  # Simple count-based popularity
            engagement_score = unique_users  # Unique user count

            item_features = {
                'item_id': item_id,
                'total_interactions': total_interactions,
                'unique_users': unique_users,
                'avg_rating': avg_rating,
                'rating_count': rating_count,
                'last_interaction': last_interaction.isoformat(),
                'first_interaction': first_interaction.isoformat(),
                'popularity_score': popularity_score,
                'engagement_score': engagement_score,
                'num_views': interaction_types.get('view', 0),
                'num_clicks': interaction_types.get('click', 0),
                'num_purchases': interaction_types.get('purchase', 0),
                'num_likes': interaction_types.get('like', 0),
                'num_cart_adds': interaction_types.get('add_to_cart', 0),
                'purchase_rate': interaction_types.get('purchase', 0) / total_interactions if total_interactions > 0 else 0,
                'click_through_rate': interaction_types.get('click', 0) / max(interaction_types.get('view', 1), 1),
            }

            item_stats.append(item_features)

        item_features_df = pd.DataFrame(item_stats)

        # Merge with item metadata if provided
        if items_df is not None and not items_df.empty:
            item_features_df = item_features_df.merge(
                items_df,
                on='item_id',
                how='left'
            )

        logger.info(f"Computed features for {len(item_features_df)} items")

        return item_features_df

    def compute_interaction_features(
        self,
        interactions_df: pd.DataFrame,
        user_features_df: pd.DataFrame,
        item_features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute interaction-level features by joining user and item features.

        Args:
            interactions_df: Raw interaction data
            user_features_df: User features
            item_features_df: Item features

        Returns:
            Enhanced interaction DataFrame with features
        """
        logger.info(f"Computing interaction features for {len(interactions_df)} interactions")

        # Start with interactions
        enriched_df = interactions_df.copy()

        # Add user features
        user_feature_cols = [col for col in user_features_df.columns if col not in ['user_id', 'recent_items']]
        enriched_df = enriched_df.merge(
            user_features_df[user_feature_cols],
            on='user_id',
            how='left',
            suffixes=('', '_user')
        )

        # Add item features
        item_feature_cols = [col for col in item_features_df.columns if col != 'item_id']
        enriched_df = enriched_df.merge(
            item_features_df[item_feature_cols],
            on='item_id',
            how='left',
            suffixes=('', '_item')
        )

        logger.info(f"Enriched {len(enriched_df)} interactions with features")

        return enriched_df

    def save_features(
        self,
        user_features_df: pd.DataFrame,
        item_features_df: pd.DataFrame,
        timestamp: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Save computed features to S3.

        Args:
            user_features_df: User features
            item_features_df: Item features
            timestamp: Optional timestamp for versioning

        Returns:
            Dictionary with S3 keys
        """
        if timestamp is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        # Save user features
        user_key = f"features/users/user_features_{timestamp}.parquet"
        s3_client.upload_dataframe(
            user_features_df,
            settings.s3_bucket_features,
            user_key,
            format='parquet'
        )

        # Save item features
        item_key = f"features/items/item_features_{timestamp}.parquet"
        s3_client.upload_dataframe(
            item_features_df,
            settings.s3_bucket_features,
            item_key,
            format='parquet'
        )

        logger.info(
            f"Saved features to S3: {user_key}, {item_key}"
        )

        return {
            'user_features_key': user_key,
            'item_features_key': item_key,
            'timestamp': timestamp
        }

    def load_features(
        self,
        timestamp: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Load features from S3.

        Args:
            timestamp: Optional timestamp to load specific version. If None, loads latest.

        Returns:
            Dictionary with 'user_features' and 'item_features' DataFrames
        """
        # If no timestamp provided, find latest
        if timestamp is None:
            user_keys = s3_client.list_objects(
                settings.s3_bucket_features,
                prefix='features/users/'
            )
            if user_keys:
                user_key = sorted(user_keys)[-1]
            else:
                raise FileNotFoundError("No user features found in S3")

            item_keys = s3_client.list_objects(
                settings.s3_bucket_features,
                prefix='features/items/'
            )
            if item_keys:
                item_key = sorted(item_keys)[-1]
            else:
                raise FileNotFoundError("No item features found in S3")
        else:
            user_key = f"features/users/user_features_{timestamp}.parquet"
            item_key = f"features/items/item_features_{timestamp}.parquet"

        # Load DataFrames
        user_features_df = s3_client.download_dataframe(
            settings.s3_bucket_features,
            user_key,
            format='parquet'
        )

        item_features_df = s3_client.download_dataframe(
            settings.s3_bucket_features,
            item_key,
            format='parquet'
        )

        logger.info(f"Loaded features from S3: {user_key}, {item_key}")

        return {
            'user_features': user_features_df,
            'item_features': item_features_df
        }
