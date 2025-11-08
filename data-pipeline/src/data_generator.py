"""Generate realistic sample data for testing and demonstration."""
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generate realistic e-commerce data."""

    def __init__(
        self,
        num_users: int = 10000,
        num_items: int = 5000,
        num_interactions: int = 100000,
        seed: int = 42
    ):
        """
        Initialize data generator.

        Args:
            num_users: Number of users to generate
            num_items: Number of items to generate
            num_interactions: Number of interactions to generate
            seed: Random seed for reproducibility
        """
        self.num_users = num_users
        self.num_items = num_items
        self.num_interactions = num_interactions
        self.seed = seed

        random.seed(seed)
        np.random.seed(seed)

        # E-commerce categories and brands
        self.categories = [
            "Electronics", "Smartphones", "Laptops", "Tablets",
            "Audio", "Headphones", "Speakers", "Cameras",
            "Wearables", "Smart Home", "Gaming", "Accessories"
        ]

        self.brands = [
            "Apple", "Samsung", "Sony", "LG", "Bose",
            "JBL", "Canon", "Nikon", "Dell", "HP",
            "Lenovo", "Asus", "Microsoft", "Google", "Amazon"
        ]

        self.interaction_types = [
            "view", "click", "purchase", "like", "add_to_cart"
        ]

        # Interaction type probabilities (view is most common, purchase is rare)
        self.interaction_probs = [0.50, 0.25, 0.08, 0.12, 0.05]

    def generate_items(self) -> pd.DataFrame:
        """
        Generate item catalog data.

        Returns:
            DataFrame with item data
        """
        logger.info(f"Generating {self.num_items} items")

        items = []

        product_names = [
            "Wireless Headphones", "Smart Watch", "Laptop", "Smartphone",
            "Tablet", "Camera", "Speaker", "Earbuds", "Monitor",
            "Keyboard", "Mouse", "Charger", "Case", "Stand"
        ]

        adjectives = [
            "Premium", "Pro", "Ultra", "Max", "Mini", "Lite",
            "Elite", "Plus", "Essential", "Advanced", "Smart"
        ]

        for i in range(self.num_items):
            item_id = f"item_{i+1:05d}"
            category = random.choice(self.categories)
            brand = random.choice(self.brands)
            product = random.choice(product_names)
            adjective = random.choice(adjectives) if random.random() > 0.5 else ""

            title = f"{brand} {adjective} {product}".strip()
            price = round(random.uniform(9.99, 1999.99), 2)

            items.append({
                "item_id": item_id,
                "title": title,
                "category": category,
                "price": price,
                "brand": brand,
            })

        items_df = pd.DataFrame(items)
        logger.info(f"Generated {len(items_df)} items")

        return items_df

    def generate_interactions(
        self,
        items_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate interaction data with realistic patterns.

        Uses Zipf distribution to simulate the 80/20 rule:
        - Popular items get more interactions
        - Active users generate more interactions

        Args:
            items_df: Item catalog DataFrame

        Returns:
            DataFrame with interaction data
        """
        logger.info(f"Generating {self.num_interactions} interactions")

        interactions = []

        # Create user IDs
        user_ids = [f"user_{i+1:05d}" for i in range(self.num_users)]

        # Create item IDs list from items_df
        item_ids = items_df['item_id'].tolist()

        # Generate Zipf distribution for items (80/20 rule)
        # Some items are much more popular than others
        item_popularity = np.random.zipf(1.5, len(item_ids))
        item_weights = item_popularity / item_popularity.sum()
        # Ensure weights sum to exactly 1.0 to avoid floating point errors
        item_weights = item_weights / item_weights.sum()

        # Generate Zipf distribution for users
        # Some users are much more active than others
        user_activity = np.random.zipf(1.3, len(user_ids))
        user_weights = user_activity / user_activity.sum()
        # Ensure weights sum to exactly 1.0 to avoid floating point errors
        user_weights = user_weights / user_weights.sum()

        # Generate timestamps over the last 90 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        for _ in range(self.num_interactions):
            # Select user (weighted by activity)
            user_id = np.random.choice(user_ids, p=user_weights)

            # Select item (weighted by popularity)
            item_id = np.random.choice(item_ids, p=item_weights)

            # Select interaction type (weighted)
            interaction_type = np.random.choice(
                self.interaction_types,
                p=self.interaction_probs
            )

            # Generate timestamp
            random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
            timestamp = start_date + timedelta(seconds=random_seconds)

            # Add rating for purchase interactions
            rating = None
            if interaction_type == "purchase" and random.random() > 0.3:
                rating = random.choice([3.0, 4.0, 5.0, 4.5, 3.5])

            interactions.append({
                "user_id": user_id,
                "item_id": item_id,
                "interaction_type": interaction_type,
                "timestamp": timestamp.isoformat(),
                "rating": rating,
            })

        interactions_df = pd.DataFrame(interactions)

        # Sort by timestamp
        interactions_df = interactions_df.sort_values('timestamp').reset_index(drop=True)

        logger.info(
            f"Generated {len(interactions_df)} interactions "
            f"({interactions_df['user_id'].nunique()} unique users, "
            f"{interactions_df['item_id'].nunique()} unique items)"
        )

        return interactions_df

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """
        Generate both items and interactions.

        Returns:
            Dictionary with 'items' and 'interactions' DataFrames
        """
        logger.info("Generating sample data...")

        items_df = self.generate_items()
        interactions_df = self.generate_interactions(items_df)

        logger.info("Sample data generation complete!")

        return {
            "items": items_df,
            "interactions": interactions_df
        }

    def save_to_csv(
        self,
        output_dir: str = "./sample_data"
    ):
        """
        Generate and save sample data to CSV files.

        Args:
            output_dir: Directory to save CSV files
        """
        import os

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate data
        data = self.generate_all()

        # Save to CSV
        items_path = os.path.join(output_dir, "items.csv")
        interactions_path = os.path.join(output_dir, "interactions.csv")

        data["items"].to_csv(items_path, index=False)
        data["interactions"].to_csv(interactions_path, index=False)

        logger.info(f"Saved items to {items_path}")
        logger.info(f"Saved interactions to {interactions_path}")

        # Print statistics
        print("\n" + "="*60)
        print("SAMPLE DATA GENERATION COMPLETE")
        print("="*60)
        print(f"Items: {len(data['items'])} products")
        print(f"Users: {data['interactions']['user_id'].nunique()} unique users")
        print(f"Interactions: {len(data['interactions'])} total")
        print(f"\nInteraction breakdown:")
        print(data['interactions']['interaction_type'].value_counts())
        print(f"\nCategory breakdown:")
        print(data['items']['category'].value_counts())
        print(f"\nFiles saved to: {output_dir}")
        print("="*60 + "\n")

        return {
            "items_path": items_path,
            "interactions_path": interactions_path
        }


def main():
    """Main function to generate sample data."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate sample e-commerce data")
    parser.add_argument("--users", type=int, default=10000, help="Number of users")
    parser.add_argument("--items", type=int, default=5000, help="Number of items")
    parser.add_argument("--interactions", type=int, default=100000, help="Number of interactions")
    parser.add_argument("--output", type=str, default="./sample_data", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Generate data
    generator = SampleDataGenerator(
        num_users=args.users,
        num_items=args.items,
        num_interactions=args.interactions,
        seed=args.seed
    )

    generator.save_to_csv(output_dir=args.output)


if __name__ == "__main__":
    main()
