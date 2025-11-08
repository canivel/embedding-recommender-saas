"""Negative sampling for training data generation."""
import logging
from typing import Dict, Any, List, Set
from datetime import datetime
import pandas as pd
import numpy as np

from ..config import settings
from ..storage.s3_client import s3_client

logger = logging.getLogger(__name__)


class NegativeSampler:
    """Generate negative samples for training."""

    def __init__(self, negative_ratio: int = 4):
        """
        Initialize negative sampler.

        Args:
            negative_ratio: Number of negative samples per positive sample
        """
        self.negative_ratio = negative_ratio

    def generate_training_data(
        self,
        interactions_df: pd.DataFrame,
        items_df: Optional[pd.DataFrame] = None,
        positive_interaction_types: List[str] = None
    ) -> pd.DataFrame:
        """
        Generate training data with positive and negative samples.

        Args:
            interactions_df: DataFrame with interaction data
            items_df: Optional DataFrame with item catalog (for sampling pool)
            positive_interaction_types: List of interaction types considered positive.
                                       Defaults to ['click', 'purchase', 'like']

        Returns:
            DataFrame with columns: user_id, item_id, label (1.0 for positive, 0.0 for negative)
        """
        if positive_interaction_types is None:
            positive_interaction_types = ['click', 'purchase', 'like']

        logger.info(
            f"Generating training data from {len(interactions_df)} interactions "
            f"with negative ratio {self.negative_ratio}:1"
        )

        # Filter positive interactions
        positive_df = interactions_df[
            interactions_df['interaction_type'].isin(positive_interaction_types)
        ].copy()

        logger.info(f"Found {len(positive_df)} positive interactions")

        if len(positive_df) == 0:
            logger.warning("No positive interactions found!")
            return pd.DataFrame(columns=['user_id', 'item_id', 'label'])

        # Create positive samples
        positive_samples = positive_df[['user_id', 'item_id']].copy()
        positive_samples['label'] = 1.0

        # Get all unique items
        if items_df is not None and not items_df.empty:
            all_items = set(items_df['item_id'].unique())
        else:
            all_items = set(interactions_df['item_id'].unique())

        logger.info(f"Sampling from pool of {len(all_items)} items")

        # Build user interaction history (items they've interacted with)
        user_item_history = {}
        for user_id, group in interactions_df.groupby('user_id'):
            user_item_history[user_id] = set(group['item_id'].unique())

        # Generate negative samples
        negative_samples = []

        for user_id in positive_samples['user_id'].unique():
            # Get items user has interacted with
            interacted_items = user_item_history.get(user_id, set())

            # Candidate items for negative sampling (items user hasn't seen)
            candidate_items = list(all_items - interacted_items)

            if len(candidate_items) == 0:
                logger.warning(f"User {user_id} has interacted with all items, skipping")
                continue

            # Number of positive samples for this user
            num_positive = len(positive_samples[positive_samples['user_id'] == user_id])

            # Number of negative samples to generate
            num_negative = num_positive * self.negative_ratio

            # Sample negative items
            if len(candidate_items) < num_negative:
                # If not enough candidates, sample with replacement
                sampled_items = np.random.choice(
                    candidate_items,
                    size=num_negative,
                    replace=True
                )
            else:
                # Sample without replacement
                sampled_items = np.random.choice(
                    candidate_items,
                    size=num_negative,
                    replace=False
                )

            for item_id in sampled_items:
                negative_samples.append({
                    'user_id': user_id,
                    'item_id': item_id,
                    'label': 0.0
                })

        negative_samples_df = pd.DataFrame(negative_samples)

        logger.info(f"Generated {len(negative_samples_df)} negative samples")

        # Combine positive and negative samples
        training_data = pd.concat([positive_samples, negative_samples_df], ignore_index=True)

        # Shuffle the data
        training_data = training_data.sample(frac=1.0, random_state=42).reset_index(drop=True)

        logger.info(
            f"Generated training data: {len(training_data)} total samples "
            f"({len(positive_samples)} positive, {len(negative_samples_df)} negative)"
        )

        return training_data

    def generate_training_data_with_features(
        self,
        interactions_df: pd.DataFrame,
        user_features_df: pd.DataFrame,
        item_features_df: pd.DataFrame,
        items_df: Optional[pd.DataFrame] = None,
        positive_interaction_types: List[str] = None
    ) -> pd.DataFrame:
        """
        Generate training data with features attached.

        Args:
            interactions_df: Interaction data
            user_features_df: User features
            item_features_df: Item features
            items_df: Optional item catalog
            positive_interaction_types: List of positive interaction types

        Returns:
            Training data with features
        """
        # Generate basic training data
        training_data = self.generate_training_data(
            interactions_df,
            items_df,
            positive_interaction_types
        )

        if len(training_data) == 0:
            return training_data

        # Add user features
        user_feature_cols = [col for col in user_features_df.columns if col not in ['user_id', 'recent_items']]
        training_data = training_data.merge(
            user_features_df[user_feature_cols],
            on='user_id',
            how='left'
        )

        # Add item features
        item_feature_cols = [col for col in item_features_df.columns if col != 'item_id']
        training_data = training_data.merge(
            item_features_df[item_feature_cols],
            on='item_id',
            how='left'
        )

        logger.info(f"Attached features to training data: {training_data.shape}")

        return training_data

    def save_training_data(
        self,
        training_data: pd.DataFrame,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Save training data to S3.

        Args:
            training_data: Training data DataFrame
            timestamp: Optional timestamp for versioning

        Returns:
            S3 key where data was saved
        """
        if timestamp is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        key = f"training/training_data_{timestamp}.parquet"

        s3_client.upload_dataframe(
            training_data,
            settings.s3_bucket_training,
            key,
            format='parquet'
        )

        logger.info(f"Saved training data to S3: {key} ({len(training_data)} samples)")

        return key

    def load_training_data(
        self,
        timestamp: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load training data from S3.

        Args:
            timestamp: Optional timestamp to load specific version. If None, loads latest.

        Returns:
            Training data DataFrame
        """
        # If no timestamp provided, find latest
        if timestamp is None:
            keys = s3_client.list_objects(
                settings.s3_bucket_training,
                prefix='training/'
            )
            if not keys:
                raise FileNotFoundError("No training data found in S3")

            key = sorted(keys)[-1]
        else:
            key = f"training/training_data_{timestamp}.parquet"

        # Load DataFrame
        training_data = s3_client.download_dataframe(
            settings.s3_bucket_training,
            key,
            format='parquet'
        )

        logger.info(f"Loaded training data from S3: {key} ({len(training_data)} samples)")

        return training_data

    def split_train_test(
        self,
        training_data: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, pd.DataFrame]:
        """
        Split training data into train and test sets.

        Args:
            training_data: Full training data
            test_size: Proportion of data for testing
            random_state: Random seed

        Returns:
            Dictionary with 'train' and 'test' DataFrames
        """
        # Shuffle data
        shuffled_data = training_data.sample(frac=1.0, random_state=random_state)

        # Split
        split_idx = int(len(shuffled_data) * (1 - test_size))
        train_data = shuffled_data.iloc[:split_idx].reset_index(drop=True)
        test_data = shuffled_data.iloc[split_idx:].reset_index(drop=True)

        logger.info(
            f"Split data: {len(train_data)} train samples, {len(test_data)} test samples"
        )

        return {
            'train': train_data,
            'test': test_data
        }
