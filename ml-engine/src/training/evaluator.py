"""Evaluation metrics for recommendation systems."""

import numpy as np
import torch
from typing import List, Dict, Set, Tuple
from collections import defaultdict


class RecommenderEvaluator:
    """Evaluator for recommendation systems.

    This class computes standard recommendation metrics including:
    - NDCG@K (Normalized Discounted Cumulative Gain)
    - Precision@K
    - Recall@K
    - MAP@K (Mean Average Precision)
    - Hit Rate@K
    """

    @staticmethod
    def ndcg_at_k(
        predictions: List[int],
        ground_truth: List[int],
        k: int = 10
    ) -> float:
        """Calculate Normalized Discounted Cumulative Gain at K.

        Args:
            predictions: List of predicted item IDs (ordered by relevance)
            ground_truth: List of relevant item IDs
            k: Number of top items to consider

        Returns:
            NDCG@K score
        """
        predictions = predictions[:k]
        ground_truth_set = set(ground_truth)

        # Calculate DCG
        dcg = 0.0
        for i, item_id in enumerate(predictions):
            if item_id in ground_truth_set:
                # Relevance is 1 for relevant items, 0 otherwise
                dcg += 1.0 / np.log2(i + 2)  # i+2 because indexing starts at 0

        # Calculate IDCG (ideal DCG)
        idcg = sum([1.0 / np.log2(i + 2) for i in range(min(len(ground_truth), k))])

        # Normalize
        if idcg == 0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def precision_at_k(
        predictions: List[int],
        ground_truth: Set[int],
        k: int = 10
    ) -> float:
        """Calculate Precision at K.

        Args:
            predictions: List of predicted item IDs
            ground_truth: Set of relevant item IDs
            k: Number of top items to consider

        Returns:
            Precision@K score
        """
        predictions = predictions[:k]
        if len(predictions) == 0:
            return 0.0

        num_relevant = len(set(predictions) & ground_truth)
        return num_relevant / len(predictions)

    @staticmethod
    def recall_at_k(
        predictions: List[int],
        ground_truth: Set[int],
        k: int = 10
    ) -> float:
        """Calculate Recall at K.

        Args:
            predictions: List of predicted item IDs
            ground_truth: Set of relevant item IDs
            k: Number of top items to consider

        Returns:
            Recall@K score
        """
        if len(ground_truth) == 0:
            return 0.0

        predictions = predictions[:k]
        num_relevant = len(set(predictions) & ground_truth)
        return num_relevant / len(ground_truth)

    @staticmethod
    def hit_rate_at_k(
        predictions: List[int],
        ground_truth: Set[int],
        k: int = 10
    ) -> float:
        """Calculate Hit Rate at K.

        Hit rate is 1 if at least one relevant item is in top-K, 0 otherwise.

        Args:
            predictions: List of predicted item IDs
            ground_truth: Set of relevant item IDs
            k: Number of top items to consider

        Returns:
            Hit rate (0 or 1)
        """
        predictions = predictions[:k]
        return 1.0 if len(set(predictions) & ground_truth) > 0 else 0.0

    @staticmethod
    def average_precision_at_k(
        predictions: List[int],
        ground_truth: Set[int],
        k: int = 10
    ) -> float:
        """Calculate Average Precision at K.

        Args:
            predictions: List of predicted item IDs
            ground_truth: Set of relevant item IDs
            k: Number of top items to consider

        Returns:
            Average Precision@K score
        """
        predictions = predictions[:k]
        if len(ground_truth) == 0:
            return 0.0

        num_relevant = 0
        sum_precisions = 0.0

        for i, item_id in enumerate(predictions):
            if item_id in ground_truth:
                num_relevant += 1
                precision = num_relevant / (i + 1)
                sum_precisions += precision

        if num_relevant == 0:
            return 0.0
        return sum_precisions / min(len(ground_truth), k)

    @staticmethod
    def mean_reciprocal_rank(
        predictions: List[int],
        ground_truth: Set[int]
    ) -> float:
        """Calculate Mean Reciprocal Rank.

        Args:
            predictions: List of predicted item IDs
            ground_truth: Set of relevant item IDs

        Returns:
            Reciprocal rank of first relevant item
        """
        for i, item_id in enumerate(predictions):
            if item_id in ground_truth:
                return 1.0 / (i + 1)
        return 0.0

    def evaluate_model(
        self,
        model: torch.nn.Module,
        dataset,
        k_values: List[int] = [5, 10, 20],
        device: str = "cpu"
    ) -> Dict[str, float]:
        """Evaluate a recommendation model.

        Args:
            model: Trained recommendation model
            dataset: Dataset with user-item interactions
            k_values: List of K values for metrics
            device: Device to run evaluation on

        Returns:
            Dictionary of metric names to values
        """
        model.eval()
        model.to(device)

        # Collect ground truth interactions per user
        user_items = defaultdict(set)
        for i in range(len(dataset)):
            sample = dataset[i]
            user_id = sample["user_id"].item()
            item_id = sample["item_id"].item()
            user_items[user_id].add(item_id)

        # Evaluate each user
        metrics = defaultdict(list)

        with torch.no_grad():
            for user_id in user_items.keys():
                # Get ground truth
                ground_truth = user_items[user_id]

                # Get predictions (exclude items already interacted with)
                item_scores, item_ids = model.recommend(
                    user_id,
                    k=max(k_values),
                    exclude_items=ground_truth
                )

                # Calculate metrics for each K
                for k in k_values:
                    predictions_k = item_ids[:k].tolist()
                    ground_truth_list = list(ground_truth)

                    metrics[f"ndcg@{k}"].append(
                        self.ndcg_at_k(predictions_k, ground_truth_list, k)
                    )
                    metrics[f"precision@{k}"].append(
                        self.precision_at_k(predictions_k, ground_truth, k)
                    )
                    metrics[f"recall@{k}"].append(
                        self.recall_at_k(predictions_k, ground_truth, k)
                    )
                    metrics[f"hit_rate@{k}"].append(
                        self.hit_rate_at_k(predictions_k, ground_truth, k)
                    )

                # MRR doesn't need K
                metrics["mrr"].append(
                    self.mean_reciprocal_rank(item_ids.tolist(), ground_truth)
                )

        # Average metrics across users
        avg_metrics = {
            metric_name: np.mean(values)
            for metric_name, values in metrics.items()
        }

        return avg_metrics

    def evaluate_recommendations(
        self,
        recommendations: Dict[int, List[int]],
        ground_truth: Dict[int, Set[int]],
        k_values: List[int] = [5, 10, 20]
    ) -> Dict[str, float]:
        """Evaluate pre-computed recommendations.

        Args:
            recommendations: Dict mapping user_id to list of recommended item_ids
            ground_truth: Dict mapping user_id to set of relevant item_ids
            k_values: List of K values for metrics

        Returns:
            Dictionary of metric names to average values
        """
        metrics = defaultdict(list)

        for user_id in ground_truth.keys():
            if user_id not in recommendations:
                continue

            user_recs = recommendations[user_id]
            user_truth = ground_truth[user_id]
            user_truth_list = list(user_truth)

            for k in k_values:
                metrics[f"ndcg@{k}"].append(
                    self.ndcg_at_k(user_recs, user_truth_list, k)
                )
                metrics[f"precision@{k}"].append(
                    self.precision_at_k(user_recs, user_truth, k)
                )
                metrics[f"recall@{k}"].append(
                    self.recall_at_k(user_recs, user_truth, k)
                )
                metrics[f"hit_rate@{k}"].append(
                    self.hit_rate_at_k(user_recs, user_truth, k)
                )
                metrics[f"map@{k}"].append(
                    self.average_precision_at_k(user_recs, user_truth, k)
                )

            metrics["mrr"].append(
                self.mean_reciprocal_rank(user_recs, user_truth)
            )

        # Average metrics
        avg_metrics = {
            metric_name: np.mean(values)
            for metric_name, values in metrics.items()
        }

        return avg_metrics
