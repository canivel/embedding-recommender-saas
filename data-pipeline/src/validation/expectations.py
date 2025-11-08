"""
Data Validation using Great Expectations
Validates interaction and item data quality
"""
import great_expectations as ge
try:
    from great_expectations.core.batch import RuntimeBatchRequest
except ImportError:
    RuntimeBatchRequest = None  # Placeholder for newer GE versions
try:
    from great_expectations.data_context import BaseDataContext
except ImportError:
    from great_expectations.data_context import AbstractDataContext as BaseDataContext
try:
    from great_expectations.data_context.types.base import DataContextConfig
except ImportError:
    DataContextConfig = None  # Placeholder for newer GE versions
import pandas as pd
from typing import Dict, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Enum for data types"""
    INTERACTIONS = "interactions"
    ITEMS = "items"


class DataValidator:
    """Data validation using Great Expectations"""

    def __init__(self):
        """Initialize validator with in-memory context"""
        # Create minimal in-memory context for MVP
        self.context = None
        self.setup_context()

    def setup_context(self):
        """Setup Great Expectations context"""
        # For MVP, we'll use programmatic validation without full GE setup
        logger.info("Data validator initialized")

    def validate_interactions(self, df: pd.DataFrame) -> Dict:
        """
        Validate interaction data

        Args:
            df: DataFrame containing interaction data

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Required columns check
        required_columns = ["user_id", "item_id", "interaction_type", "timestamp"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            errors.append({
                "type": "missing_columns",
                "message": f"Missing required columns: {missing_columns}"
            })
            return {"success": False, "errors": errors, "warnings": warnings}

        # Null value checks
        for col in required_columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append({
                    "type": "null_values",
                    "column": col,
                    "message": f"Column '{col}' has {null_count} null values"
                })

        # Interaction type validation
        valid_types = ["view", "click", "purchase", "like", "dislike", "add_to_cart", "remove_from_cart"]
        if "interaction_type" in df.columns:
            invalid_types = df[~df["interaction_type"].isin(valid_types)]["interaction_type"].unique()
            if len(invalid_types) > 0:
                errors.append({
                    "type": "invalid_values",
                    "column": "interaction_type",
                    "message": f"Invalid interaction types found: {invalid_types.tolist()}",
                    "valid_values": valid_types
                })

        # Data type checks
        if "user_id" in df.columns:
            non_string_count = df[df["user_id"].apply(lambda x: not isinstance(x, str))].shape[0]
            if non_string_count > 0:
                errors.append({
                    "type": "invalid_type",
                    "column": "user_id",
                    "message": f"{non_string_count} rows have non-string user_id"
                })

        if "item_id" in df.columns:
            non_string_count = df[df["item_id"].apply(lambda x: not isinstance(x, str))].shape[0]
            if non_string_count > 0:
                errors.append({
                    "type": "invalid_type",
                    "column": "item_id",
                    "message": f"{non_string_count} rows have non-string item_id"
                })

        # Timestamp validation
        if "timestamp" in df.columns:
            try:
                pd.to_datetime(df["timestamp"])
            except Exception as e:
                errors.append({
                    "type": "invalid_timestamp",
                    "column": "timestamp",
                    "message": f"Invalid timestamp format: {str(e)}"
                })

        # Duplicate check (warning only)
        if "user_id" in df.columns and "item_id" in df.columns and "timestamp" in df.columns:
            duplicates = df.duplicated(subset=["user_id", "item_id", "timestamp"], keep=False).sum()
            if duplicates > 0:
                warnings.append({
                    "type": "duplicates",
                    "message": f"Found {duplicates} duplicate interactions"
                })

        # String length validation
        if "user_id" in df.columns:
            too_long = df[df["user_id"].str.len() > 128].shape[0]
            if too_long > 0:
                errors.append({
                    "type": "value_too_long",
                    "column": "user_id",
                    "message": f"{too_long} user_ids exceed 128 characters"
                })

        if "item_id" in df.columns:
            too_long = df[df["item_id"].str.len() > 128].shape[0]
            if too_long > 0:
                errors.append({
                    "type": "value_too_long",
                    "column": "item_id",
                    "message": f"{too_long} item_ids exceed 128 characters"
                })

        success = len(errors) == 0

        return {
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(df),
            "validation_timestamp": pd.Timestamp.now().isoformat()
        }

    def validate_items(self, df: pd.DataFrame) -> Dict:
        """
        Validate item catalog data

        Args:
            df: DataFrame containing item data

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Required columns check
        required_columns = ["item_id", "title"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            errors.append({
                "type": "missing_columns",
                "message": f"Missing required columns: {missing_columns}"
            })
            return {"success": False, "errors": errors, "warnings": warnings}

        # Null value checks
        for col in required_columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append({
                    "type": "null_values",
                    "column": col,
                    "message": f"Column '{col}' has {null_count} null values"
                })

        # Data type checks
        if "item_id" in df.columns:
            non_string_count = df[df["item_id"].apply(lambda x: not isinstance(x, str))].shape[0]
            if non_string_count > 0:
                errors.append({
                    "type": "invalid_type",
                    "column": "item_id",
                    "message": f"{non_string_count} rows have non-string item_id"
                })

        if "title" in df.columns:
            non_string_count = df[df["title"].apply(lambda x: not isinstance(x, str))].shape[0]
            if non_string_count > 0:
                errors.append({
                    "type": "invalid_type",
                    "column": "title",
                    "message": f"{non_string_count} rows have non-string title"
                })

        # Duplicate check
        if "item_id" in df.columns:
            duplicates = df.duplicated(subset=["item_id"], keep=False).sum()
            if duplicates > 0:
                warnings.append({
                    "type": "duplicates",
                    "message": f"Found {duplicates} duplicate item_ids"
                })

        # String length validation
        if "item_id" in df.columns:
            too_long = df[df["item_id"].str.len() > 128].shape[0]
            if too_long > 0:
                errors.append({
                    "type": "value_too_long",
                    "column": "item_id",
                    "message": f"{too_long} item_ids exceed 128 characters"
                })

        if "title" in df.columns:
            too_long = df[df["title"].str.len() > 500].shape[0]
            if too_long > 0:
                warnings.append({
                    "type": "value_too_long",
                    "column": "title",
                    "message": f"{too_long} titles exceed 500 characters (will be truncated)"
                })

        # Category validation
        if "category" in df.columns:
            null_count = df["category"].isnull().sum()
            if null_count > 0:
                warnings.append({
                    "type": "missing_category",
                    "message": f"{null_count} items missing category"
                })

        # Tags validation
        if "tags" in df.columns:
            def validate_tags(tags):
                if pd.isna(tags):
                    return True
                if isinstance(tags, list):
                    return len(tags) <= 20
                return False

            invalid_tags = df[~df["tags"].apply(validate_tags)].shape[0]
            if invalid_tags > 0:
                errors.append({
                    "type": "invalid_tags",
                    "column": "tags",
                    "message": f"{invalid_tags} items have invalid tags (must be list with max 20 items)"
                })

        success = len(errors) == 0

        return {
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(df),
            "validation_timestamp": pd.Timestamp.now().isoformat()
        }


# Module-level validator instance
_validator = DataValidator()


def validate_dataframe(df: pd.DataFrame, data_type: DataType) -> Dict:
    """
    Validate a DataFrame based on its data type

    Args:
        df: DataFrame to validate
        data_type: Type of data (INTERACTIONS or ITEMS)

    Returns:
        Dictionary with validation results
    """
    if data_type == DataType.INTERACTIONS:
        return _validator.validate_interactions(df)
    elif data_type == DataType.ITEMS:
        return _validator.validate_items(df)
    else:
        raise ValueError(f"Unknown data type: {data_type}")


def create_validation_report(validation_result: Dict) -> str:
    """
    Create human-readable validation report

    Args:
        validation_result: Result from validate_dataframe

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("DATA VALIDATION REPORT")
    report.append("=" * 60)
    report.append(f"Timestamp: {validation_result.get('validation_timestamp', 'N/A')}")
    report.append(f"Total Rows: {validation_result.get('row_count', 0)}")
    report.append(f"Status: {'PASSED' if validation_result['success'] else 'FAILED'}")
    report.append("")

    if validation_result.get("errors"):
        report.append("ERRORS:")
        for error in validation_result["errors"]:
            report.append(f"  - {error.get('type', 'unknown')}: {error.get('message', 'no message')}")
        report.append("")

    if validation_result.get("warnings"):
        report.append("WARNINGS:")
        for warning in validation_result["warnings"]:
            report.append(f"  - {warning.get('type', 'unknown')}: {warning.get('message', 'no message')}")
        report.append("")

    report.append("=" * 60)

    return "\n".join(report)
