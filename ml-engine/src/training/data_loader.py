"""Data loading utilities for training."""
import pandas as pd
import torch
from torch.utils.data import Dataset
from typing import Tuple, Dict, Optional
import pyarrow.parquet as pq
import boto3
import logging

logger = logging.getLogger(__name__)


class InteractionDataset(Dataset):
    """Dataset for user-item interactions."""

    def __init__(self, user_ids: torch.Tensor, item_ids: torch.Tensor, labels: torch.Tensor):
        self.user_ids = user_ids
        self.item_ids = item_ids
        self.labels = labels

    def __len__(self) -> int:
        return len(self.user_ids)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return {
            "user_id": self.user_ids[idx],
            "item_id": self.item_ids[idx],
            "label": self.labels[idx],
        }


class InteractionDataLoader:
    """Loads and processes interaction data for training."""

    def __init__(
        self,
        train_split: float = 0.8,
        val_split: float = 0.1,
        test_split: float = 0.1,
        negative_sampling_ratio: int = 4,
    ):
        self.train_split = train_split
        self.val_split = val_split
        self.test_split = test_split
        self.negative_sampling_ratio = negative_sampling_ratio

    def load_from_parquet(self, path: str, s3_client: Optional[boto3.client] = None) -> pd.DataFrame:
        """Load interactions from Parquet file."""
        if path.startswith("s3://"):
            if s3_client is None:
                s3_client = boto3.client("s3")
            bucket, key = path.replace("s3://", "").split("/", 1)
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            df = pd.read_parquet(obj["Body"])
        else:
            df = pd.read_parquet(path)
        return df

    def create_graph_data(self, df: pd.DataFrame) -> Tuple[torch.Tensor, Dict[str, int], Dict[str, int]]:
        """Create graph structure from interactions."""
        unique_users = df["user_id"].unique()
        unique_items = df["item_id"].unique()

        user_mapping = {user_id: idx for idx, user_id in enumerate(unique_users)}
        item_mapping = {item_id: idx for idx, item_id in enumerate(unique_items)}

        user_indices = df["user_id"].map(user_mapping).values
        item_indices = df["item_id"].map(item_mapping).values

        num_users = len(user_mapping)
        item_indices_offset = item_indices + num_users

        edge_index = torch.tensor(
            [[user_indices, item_indices_offset], [item_indices_offset, user_indices]],
            dtype=torch.long,
        ).reshape(2, -1)

        return edge_index, user_mapping, item_mapping

    def split_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data into train/val/test sets."""
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        n = len(df)
        train_end = int(n * self.train_split)
        val_end = int(n * (self.train_split + self.val_split))

        train_df = df[:train_end]
        val_df = df[train_end:val_end]
        test_df = df[val_end:]

        logger.info(f"Split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
        return train_df, val_df, test_df


def load_training_data(data_path: str, batch_size: int = 1024, **kwargs) -> Dict:
    """Load and prepare training data."""
    loader = InteractionDataLoader(**kwargs)
    logger.info(f"Loading data from {data_path}")
    df = loader.load_from_parquet(data_path)
    train_df, val_df, test_df = loader.split_data(df)
    edge_index, user_mapping, item_mapping = loader.create_graph_data(train_df)

    num_users = len(user_mapping)
    num_items = len(item_mapping)

    logger.info(f"Graph: {num_users} users, {num_items} items, {edge_index.shape[1]} edges")

    return {
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "edge_index": edge_index,
        "num_users": num_users,
        "num_items": num_items,
        "user_mapping": user_mapping,
        "item_mapping": item_mapping,
        "batch_size": batch_size,
    }
