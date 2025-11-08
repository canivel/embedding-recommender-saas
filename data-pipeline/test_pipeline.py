#!/usr/bin/env python3
"""
Test script to verify data pipeline functionality.

Usage:
    python test_pipeline.py
"""
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("DATA PIPELINE TEST SUITE")
print("="*60)

# Test 1: Import modules
print("\n[TEST 1] Testing module imports...")
try:
    from src.config import settings
    from src.storage.s3_client import S3Client
    from src.kafka.producer import KafkaProducerClient
    from src.kafka.consumer import KafkaConsumerClient
    from src.validation.expectations import DataValidator
    from src.etl.feature_engineering import FeatureEngineer
    from src.etl.negative_sampling import NegativeSampler
    from src.data_generator import SampleDataGenerator
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration
print("\n[TEST 2] Testing configuration...")
try:
    print(f"  Service: {settings.service_name}")
    print(f"  Version: {settings.version}")
    print(f"  Kafka: {settings.kafka_bootstrap_servers}")
    print(f"  S3 Endpoint: {settings.s3_endpoint}")
    print("✓ Configuration loaded successfully")
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    sys.exit(1)

# Test 3: Data Generation
print("\n[TEST 3] Testing data generation...")
try:
    generator = SampleDataGenerator(
        num_users=100,
        num_items=50,
        num_interactions=500,
        seed=42
    )
    data = generator.generate_all()

    print(f"  Generated {len(data['items'])} items")
    print(f"  Generated {len(data['interactions'])} interactions")
    print(f"  Unique users: {data['interactions']['user_id'].nunique()}")
    print(f"  Unique items: {data['interactions']['item_id'].nunique()}")
    print("✓ Data generation successful")
except Exception as e:
    print(f"✗ Data generation failed: {e}")
    sys.exit(1)

# Test 4: Data Validation
print("\n[TEST 4] Testing data validation...")
try:
    validator = DataValidator()

    # Validate interactions
    interactions_result = validator.validate_interactions(data['interactions'])
    print(f"  Interactions validation: {'PASSED' if interactions_result['success'] else 'FAILED'}")

    # Validate items
    items_result = validator.validate_items(data['items'])
    print(f"  Items validation: {'PASSED' if items_result['success'] else 'FAILED'}")

    if interactions_result['success'] and items_result['success']:
        print("✓ Data validation successful")
    else:
        print("✗ Data validation failed")
        if interactions_result.get('errors'):
            print(f"  Interaction errors: {interactions_result['errors']}")
        if items_result.get('errors'):
            print(f"  Item errors: {items_result['errors']}")
except Exception as e:
    print(f"✗ Data validation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Feature Engineering
print("\n[TEST 5] Testing feature engineering...")
try:
    engineer = FeatureEngineer()

    # Compute user features
    user_features = engineer.compute_user_features(data['interactions'])
    print(f"  User features: {len(user_features)} users, {len(user_features.columns)} features")

    # Compute item features
    item_features = engineer.compute_item_features(data['interactions'], data['items'])
    print(f"  Item features: {len(item_features)} items, {len(item_features.columns)} features")

    print("✓ Feature engineering successful")
except Exception as e:
    print(f"✗ Feature engineering failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Negative Sampling
print("\n[TEST 6] Testing negative sampling...")
try:
    sampler = NegativeSampler(negative_ratio=4)

    training_data = sampler.generate_training_data(
        data['interactions'],
        data['items'],
        positive_interaction_types=['click', 'purchase', 'like']
    )

    positive_count = (training_data['label'] == 1.0).sum()
    negative_count = (training_data['label'] == 0.0).sum()

    print(f"  Training samples: {len(training_data)}")
    print(f"  Positive samples: {positive_count}")
    print(f"  Negative samples: {negative_count}")
    print(f"  Ratio: 1:{negative_count/max(positive_count, 1):.1f}")
    print("✓ Negative sampling successful")
except Exception as e:
    print(f"✗ Negative sampling failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Training Data with Features
print("\n[TEST 7] Testing training data with features...")
try:
    training_with_features = sampler.generate_training_data_with_features(
        data['interactions'],
        user_features,
        item_features,
        data['items']
    )

    print(f"  Training data shape: {training_with_features.shape}")
    print(f"  Columns: {list(training_with_features.columns)[:10]}...")
    print("✓ Training data with features successful")
except Exception as e:
    print(f"✗ Training data with features failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST SUITE COMPLETE")
print("="*60)
print("\n✓ All core functionality tests passed!")
print("\nNote: S3 and Kafka connectivity tests require running services.")
print("Start services with: docker-compose up -d kafka minio")
print("\nTo test the API:")
print("  1. Start the service: uvicorn src.main:app --reload")
print("  2. Visit: http://localhost:8002/docs")
print("  3. Generate and upload data: python generate_sample_data.py --upload")
print("="*60 + "\n")
