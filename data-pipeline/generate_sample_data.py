#!/usr/bin/env python3
"""
Script to generate and optionally upload sample data to the data pipeline.

Usage:
    # Generate sample data only
    python generate_sample_data.py

    # Generate and upload to local service
    python generate_sample_data.py --upload

    # Custom parameters
    python generate_sample_data.py --users 5000 --items 2000 --interactions 50000
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_generator import SampleDataGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def upload_to_api(items_path: str, interactions_path: str, base_url: str, tenant_id: str):
    """
    Upload generated CSV files to the data pipeline API.

    Args:
        items_path: Path to items CSV file
        interactions_path: Path to interactions CSV file
        base_url: Base URL of the data pipeline service
        tenant_id: Tenant identifier
    """
    import httpx

    logger.info(f"Uploading data to {base_url}")

    # Upload items
    logger.info(f"Uploading items from {items_path}")
    with open(items_path, 'rb') as f:
        response = httpx.post(
            f"{base_url}/internal/data/upload-csv",
            params={"tenant_id": tenant_id, "data_type": "items"},
            files={"file": ("items.csv", f, "text/csv")},
            timeout=300.0
        )

    if response.status_code == 200:
        result = response.json()
        logger.info(f"Items upload successful: {result['rows_accepted']} rows accepted")
    else:
        logger.error(f"Items upload failed: {response.status_code} - {response.text}")
        return False

    # Upload interactions
    logger.info(f"Uploading interactions from {interactions_path}")
    with open(interactions_path, 'rb') as f:
        response = httpx.post(
            f"{base_url}/internal/data/upload-csv",
            params={"tenant_id": tenant_id, "data_type": "interactions"},
            files={"file": ("interactions.csv", f, "text/csv")},
            timeout=300.0
        )

    if response.status_code == 200:
        result = response.json()
        logger.info(f"Interactions upload successful: {result['rows_accepted']} rows accepted")
    else:
        logger.error(f"Interactions upload failed: {response.status_code} - {response.text}")
        return False

    logger.info("Upload complete!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate sample e-commerce data for testing"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10000,
        help="Number of users to generate (default: 10000)"
    )
    parser.add_argument(
        "--items",
        type=int,
        default=5000,
        help="Number of items to generate (default: 5000)"
    )
    parser.add_argument(
        "--interactions",
        type=int,
        default=100000,
        help="Number of interactions to generate (default: 100000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./sample_data",
        help="Output directory for CSV files (default: ./sample_data)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload generated data to API after generation"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8002",
        help="Data pipeline API URL (default: http://localhost:8002)"
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="demo",
        help="Tenant ID for upload (default: demo)"
    )

    args = parser.parse_args()

    # Generate sample data
    logger.info("="*60)
    logger.info("SAMPLE DATA GENERATION")
    logger.info("="*60)
    logger.info(f"Users: {args.users}")
    logger.info(f"Items: {args.items}")
    logger.info(f"Interactions: {args.interactions}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Seed: {args.seed}")
    logger.info("="*60)

    generator = SampleDataGenerator(
        num_users=args.users,
        num_items=args.items,
        num_interactions=args.interactions,
        seed=args.seed
    )

    paths = generator.save_to_csv(output_dir=args.output)

    # Upload if requested
    if args.upload:
        logger.info("\n" + "="*60)
        logger.info("UPLOADING TO DATA PIPELINE")
        logger.info("="*60)
        logger.info(f"API URL: {args.api_url}")
        logger.info(f"Tenant ID: {args.tenant_id}")
        logger.info("="*60 + "\n")

        try:
            success = upload_to_api(
                paths["items_path"],
                paths["interactions_path"],
                args.api_url,
                args.tenant_id
            )

            if success:
                logger.info("\n" + "="*60)
                logger.info("SUCCESS!")
                logger.info("="*60)
                logger.info("Data generated and uploaded successfully")
                logger.info("="*60 + "\n")
            else:
                logger.error("\nUpload failed. Check the logs above for details.")
                sys.exit(1)

        except Exception as e:
            logger.error(f"\nUpload error: {e}")
            logger.error("Is the data pipeline service running?")
            logger.error(f"Try: curl {args.api_url}/health")
            sys.exit(1)
    else:
        logger.info("\nTo upload the generated data, run:")
        logger.info(f"  python generate_sample_data.py --upload")
        logger.info("\nOr use curl:")
        logger.info(f"  curl -X POST '{args.api_url}/internal/data/upload-csv?tenant_id={args.tenant_id}&data_type=items' \\")
        logger.info(f"    -F 'file=@{paths['items_path']}'")
        logger.info(f"  curl -X POST '{args.api_url}/internal/data/upload-csv?tenant_id={args.tenant_id}&data_type=interactions' \\")
        logger.info(f"    -F 'file=@{paths['interactions_path']}'")


if __name__ == "__main__":
    main()
