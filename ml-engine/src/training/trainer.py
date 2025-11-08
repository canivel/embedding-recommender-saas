"""Model training utilities."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Dict, Optional, Callable
import time
from pathlib import Path
import json


class ModelTrainer:
    """Trainer for recommendation models.

    Args:
        model: PyTorch model to train
        optimizer: PyTorch optimizer
        criterion: Loss function
        device: Device to train on ('cuda' or 'cpu')
        gradient_clip: Maximum gradient norm for clipping (default: None)
    """

    def __init__(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: str = "cpu",
        gradient_clip: Optional[float] = None
    ):
        self.model = model.to(device)
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.gradient_clip = gradient_clip

        self.train_losses = []
        self.val_losses = []
        self.best_val_loss = float("inf")

    def train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch.

        Args:
            train_loader: DataLoader for training data

        Returns:
            Average training loss for the epoch
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in train_loader:
            # Move data to device
            user_ids = batch["user_id"].to(self.device)
            item_ids = batch["item_id"].to(self.device)
            ratings = batch["rating"].to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            predictions = self.model(user_ids, item_ids)
            loss = self.criterion(predictions, ratings)

            # Backward pass
            loss.backward()

            # Gradient clipping
            if self.gradient_clip is not None:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.gradient_clip
                )

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        return avg_loss

    def evaluate(self, data_loader: DataLoader) -> float:
        """Evaluate model on a dataset.

        Args:
            data_loader: DataLoader for evaluation data

        Returns:
            Average loss on the dataset
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in data_loader:
                user_ids = batch["user_id"].to(self.device)
                item_ids = batch["item_id"].to(self.device)
                ratings = batch["rating"].to(self.device)

                predictions = self.model(user_ids, item_ids)
                loss = self.criterion(predictions, ratings)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        return avg_loss

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        num_epochs: int = 10,
        early_stopping_patience: Optional[int] = None,
        verbose: bool = True,
        checkpoint_dir: Optional[str] = None
    ) -> Dict[str, list]:
        """Train the model.

        Args:
            train_loader: DataLoader for training data
            val_loader: Optional DataLoader for validation data
            num_epochs: Number of training epochs
            early_stopping_patience: Stop if no improvement for N epochs
            verbose: Whether to print progress
            checkpoint_dir: Directory to save checkpoints

        Returns:
            Dictionary with training history
        """
        history = {"train_loss": [], "val_loss": [], "epoch_time": []}
        patience_counter = 0

        for epoch in range(num_epochs):
            epoch_start = time.time()

            # Training
            train_loss = self.train_epoch(train_loader)
            history["train_loss"].append(train_loss)

            # Validation
            if val_loader is not None:
                val_loss = self.evaluate(val_loader)
                history["val_loss"].append(val_loss)

                # Early stopping
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    patience_counter = 0

                    # Save best model
                    if checkpoint_dir is not None:
                        self.save_checkpoint(
                            Path(checkpoint_dir) / "best_model.pt",
                            epoch,
                            val_loss
                        )
                else:
                    patience_counter += 1

                if early_stopping_patience and patience_counter >= early_stopping_patience:
                    if verbose:
                        print(f"Early stopping at epoch {epoch + 1}")
                    break
            else:
                val_loss = None

            epoch_time = time.time() - epoch_start
            history["epoch_time"].append(epoch_time)

            # Print progress
            if verbose:
                msg = f"Epoch {epoch + 1}/{num_epochs} - "
                msg += f"Train Loss: {train_loss:.4f}"
                if val_loss is not None:
                    msg += f", Val Loss: {val_loss:.4f}"
                msg += f", Time: {epoch_time:.2f}s"
                print(msg)

        return history

    def save_checkpoint(
        self,
        path: str,
        epoch: int,
        loss: float,
        metadata: Optional[Dict] = None
    ) -> None:
        """Save model checkpoint.

        Args:
            path: Path to save checkpoint
            epoch: Current epoch number
            loss: Current loss value
            metadata: Optional metadata to save with checkpoint
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "loss": loss,
            "metadata": metadata or {}
        }

        torch.save(checkpoint, path)

    def load_checkpoint(self, path: str) -> Dict:
        """Load model checkpoint.

        Args:
            path: Path to checkpoint file

        Returns:
            Checkpoint dictionary
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        return checkpoint


def train_matrix_factorization(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: Optional[DataLoader] = None,
    num_epochs: int = 10,
    learning_rate: float = 0.001,
    weight_decay: float = 0.01,
    device: str = "cpu",
    verbose: bool = True,
    checkpoint_dir: Optional[str] = None
) -> Dict:
    """Convenience function to train a Matrix Factorization model.

    Args:
        model: MatrixFactorization model
        train_loader: Training data loader
        val_loader: Validation data loader
        num_epochs: Number of training epochs
        learning_rate: Learning rate for optimizer
        weight_decay: L2 regularization parameter
        device: Device to train on
        verbose: Whether to print progress
        checkpoint_dir: Directory to save checkpoints

    Returns:
        Training history dictionary
    """
    # Setup optimizer and loss
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay
    )
    criterion = nn.MSELoss()

    # Create trainer
    trainer = ModelTrainer(
        model=model,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        gradient_clip=5.0
    )

    # Train
    history = trainer.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
        early_stopping_patience=5,
        verbose=verbose,
        checkpoint_dir=checkpoint_dir
    )

    return history
