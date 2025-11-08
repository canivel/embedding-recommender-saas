"""
Tenant Model Training DAG

This DAG orchestrates the end-to-end training pipeline for tenant-specific models:
1. Validates that training data exists in S3/MinIO
2. Triggers ML Engine training via HTTP API
3. Polls for training completion
4. Builds FAISS index for fast similarity search
5. Deploys model to production
6. Updates Redis cache with new embeddings

Schedule: Daily at 2 AM (can be triggered manually)
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import time
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowException
import requests


# Default arguments for the DAG
default_args = {
    'owner': 'control-plane',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=6),
}

# DAG definition
dag = DAG(
    'tenant_model_training',
    default_args=default_args,
    description='Train tenant-specific embedding models and deploy to production',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'training', 'tenant'],
)


def validate_training_data(**context) -> Dict[str, Any]:
    """
    Validate that training data exists in S3/MinIO for the tenant.

    Returns:
        Dict containing validation results and data location
    """
    tenant_id = context['dag_run'].conf.get('tenant_id', 'default_tenant')
    data_path = f"training-data/{tenant_id}/latest/"

    print(f"Validating training data for tenant: {tenant_id}")
    print(f"Expected data path: {data_path}")

    try:
        # Initialize S3 hook (MinIO compatible)
        s3_hook = S3Hook(aws_conn_id='minio_default')

        # Check if bucket exists
        bucket_name = 'embeddings-training-data'
        if not s3_hook.check_for_bucket(bucket_name):
            raise AirflowException(f"Bucket {bucket_name} does not exist")

        # List objects in the training data path
        keys = s3_hook.list_keys(bucket_name=bucket_name, prefix=data_path)

        if not keys or len(keys) == 0:
            raise AirflowException(f"No training data found at {data_path}")

        # Count data files
        data_files = [k for k in keys if k.endswith(('.json', '.jsonl', '.parquet'))]

        if len(data_files) == 0:
            raise AirflowException(f"No valid data files found at {data_path}")

        # Calculate total size
        total_size = 0
        for key in data_files:
            obj = s3_hook.get_key(key, bucket_name=bucket_name)
            total_size += obj.content_length if hasattr(obj, 'content_length') else 0

        validation_result = {
            'tenant_id': tenant_id,
            'data_path': data_path,
            'bucket_name': bucket_name,
            'file_count': len(data_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': data_files[:10],  # First 10 files
            'validation_timestamp': datetime.now().isoformat(),
        }

        print(f"Validation successful: {json.dumps(validation_result, indent=2)}")

        # Push to XCom for downstream tasks
        context['task_instance'].xcom_push(key='validation_result', value=validation_result)

        return validation_result

    except Exception as e:
        raise AirflowException(f"Training data validation failed: {str(e)}")


def trigger_ml_training(**context) -> str:
    """
    Trigger ML Engine training via HTTP API.

    Returns:
        Job ID for tracking training progress
    """
    # Get validation results from previous task
    validation_result = context['task_instance'].xcom_pull(
        task_ids='validate_training_data',
        key='validation_result'
    )

    tenant_id = validation_result['tenant_id']
    data_path = validation_result['data_path']

    print(f"Triggering training for tenant: {tenant_id}")

    # ML Engine API endpoint
    ml_engine_url = "http://ml-engine:8000/api/v1/train"

    # Training configuration
    training_config = {
        'tenant_id': tenant_id,
        'data_source': {
            'type': 's3',
            'bucket': validation_result['bucket_name'],
            'path': data_path,
        },
        'model_config': {
            'model_type': 'sentence-transformer',
            'base_model': 'all-MiniLM-L6-v2',
            'max_seq_length': 256,
            'batch_size': 32,
            'epochs': 3,
        },
        'output_path': f"models/{tenant_id}/",
    }

    try:
        response = requests.post(
            ml_engine_url,
            json=training_config,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        job_id = result.get('job_id')

        if not job_id:
            raise AirflowException("No job_id returned from ML Engine")

        print(f"Training job started: {job_id}")

        # Push job_id to XCom
        context['task_instance'].xcom_push(key='job_id', value=job_id)

        return job_id

    except requests.exceptions.RequestException as e:
        raise AirflowException(f"Failed to trigger ML training: {str(e)}")


def wait_for_training_completion(**context) -> Dict[str, Any]:
    """
    Poll ML Engine for training completion status.

    Returns:
        Training results including model location
    """
    job_id = context['task_instance'].xcom_pull(
        task_ids='trigger_ml_training',
        key='job_id'
    )

    print(f"Waiting for training job: {job_id}")

    status_url = f"http://ml-engine:8000/api/v1/jobs/{job_id}/status"
    max_attempts = 360  # 6 hours with 1-minute intervals
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(status_url, timeout=10)
            response.raise_for_status()

            status_data = response.json()
            status = status_data.get('status')

            print(f"Attempt {attempt + 1}/{max_attempts}: Status = {status}")

            if status == 'completed':
                print("Training completed successfully!")
                context['task_instance'].xcom_push(key='training_result', value=status_data)
                return status_data

            elif status == 'failed':
                error_msg = status_data.get('error', 'Unknown error')
                raise AirflowException(f"Training failed: {error_msg}")

            elif status in ['pending', 'running']:
                # Still in progress, wait and retry
                time.sleep(60)  # Wait 1 minute
                attempt += 1

            else:
                raise AirflowException(f"Unknown status: {status}")

        except requests.exceptions.RequestException as e:
            print(f"Error checking status: {str(e)}")
            time.sleep(60)
            attempt += 1

    raise AirflowException(f"Training timeout after {max_attempts} attempts")


def build_faiss_index(**context) -> Dict[str, Any]:
    """
    Build FAISS index for fast similarity search.

    Returns:
        Index metadata and location
    """
    training_result = context['task_instance'].xcom_pull(
        task_ids='wait_for_training_completion',
        key='training_result'
    )

    validation_result = context['task_instance'].xcom_pull(
        task_ids='validate_training_data',
        key='validation_result'
    )

    tenant_id = validation_result['tenant_id']
    model_path = training_result.get('model_path')

    print(f"Building FAISS index for tenant: {tenant_id}")
    print(f"Using model: {model_path}")

    # Trigger FAISS index building
    index_url = "http://ml-engine:8000/api/v1/index/build"

    index_config = {
        'tenant_id': tenant_id,
        'model_path': model_path,
        'index_type': 'IVF',
        'nlist': 100,
        'output_path': f"indices/{tenant_id}/",
    }

    try:
        response = requests.post(
            index_url,
            json=index_config,
            timeout=300  # 5 minutes timeout
        )
        response.raise_for_status()

        index_result = response.json()
        print(f"FAISS index built: {json.dumps(index_result, indent=2)}")

        context['task_instance'].xcom_push(key='index_result', value=index_result)

        return index_result

    except requests.exceptions.RequestException as e:
        raise AirflowException(f"Failed to build FAISS index: {str(e)}")


def deploy_to_production(**context) -> Dict[str, Any]:
    """
    Deploy trained model to production inference service.

    Returns:
        Deployment status and endpoint information
    """
    training_result = context['task_instance'].xcom_pull(
        task_ids='wait_for_training_completion',
        key='training_result'
    )

    index_result = context['task_instance'].xcom_pull(
        task_ids='build_faiss_index',
        key='index_result'
    )

    validation_result = context['task_instance'].xcom_pull(
        task_ids='validate_training_data',
        key='validation_result'
    )

    tenant_id = validation_result['tenant_id']
    model_path = training_result.get('model_path')
    index_path = index_result.get('index_path')

    print(f"Deploying model for tenant: {tenant_id}")

    # Deploy to inference service
    deploy_url = "http://inference-service:8001/api/v1/deploy"

    deploy_config = {
        'tenant_id': tenant_id,
        'model_path': model_path,
        'index_path': index_path,
        'version': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'config': {
            'batch_size': 64,
            'max_concurrent_requests': 100,
        }
    }

    try:
        response = requests.post(
            deploy_url,
            json=deploy_config,
            timeout=120
        )
        response.raise_for_status()

        deploy_result = response.json()
        print(f"Deployment successful: {json.dumps(deploy_result, indent=2)}")

        context['task_instance'].xcom_push(key='deploy_result', value=deploy_result)

        return deploy_result

    except requests.exceptions.RequestException as e:
        raise AirflowException(f"Failed to deploy model: {str(e)}")


def update_redis_cache(**context) -> Dict[str, Any]:
    """
    Update Redis cache with new embeddings for frequently accessed items.

    Returns:
        Cache update statistics
    """
    validation_result = context['task_instance'].xcom_pull(
        task_ids='validate_training_data',
        key='validation_result'
    )

    deploy_result = context['task_instance'].xcom_pull(
        task_ids='deploy_to_production',
        key='deploy_result'
    )

    tenant_id = validation_result['tenant_id']

    print(f"Updating Redis cache for tenant: {tenant_id}")

    # Trigger cache warming
    cache_url = "http://inference-service:8001/api/v1/cache/warm"

    cache_config = {
        'tenant_id': tenant_id,
        'top_k': 1000,  # Cache top 1000 items
        'force_refresh': True,
    }

    try:
        response = requests.post(
            cache_url,
            json=cache_config,
            timeout=180
        )
        response.raise_for_status()

        cache_result = response.json()
        print(f"Cache updated: {json.dumps(cache_result, indent=2)}")

        return cache_result

    except requests.exceptions.RequestException as e:
        # Cache update is not critical, log warning but don't fail
        print(f"Warning: Failed to update cache: {str(e)}")
        return {'status': 'skipped', 'error': str(e)}


# Task definitions
task_validate_data = PythonOperator(
    task_id='validate_training_data',
    python_callable=validate_training_data,
    dag=dag,
    doc_md="""
    ## Validate Training Data

    Checks that training data exists in S3/MinIO and meets minimum requirements.
    - Validates bucket existence
    - Counts data files
    - Calculates total data size
    """,
)

task_trigger_training = PythonOperator(
    task_id='trigger_ml_training',
    python_callable=trigger_ml_training,
    dag=dag,
    doc_md="""
    ## Trigger ML Training

    Sends training request to ML Engine via HTTP API.
    Returns job ID for tracking.
    """,
)

task_wait_completion = PythonOperator(
    task_id='wait_for_training_completion',
    python_callable=wait_for_training_completion,
    dag=dag,
    execution_timeout=timedelta(hours=6),
    doc_md="""
    ## Wait for Training Completion

    Polls ML Engine for training status.
    Max wait time: 6 hours with 1-minute intervals.
    """,
)

task_build_index = PythonOperator(
    task_id='build_faiss_index',
    python_callable=build_faiss_index,
    dag=dag,
    doc_md="""
    ## Build FAISS Index

    Creates FAISS index for fast similarity search.
    Uses IVF (Inverted File) indexing for efficiency.
    """,
)

task_deploy = PythonOperator(
    task_id='deploy_to_production',
    python_callable=deploy_to_production,
    dag=dag,
    doc_md="""
    ## Deploy to Production

    Deploys trained model to inference service.
    Creates versioned deployment for rollback capability.
    """,
)

task_update_cache = PythonOperator(
    task_id='update_redis_cache',
    python_callable=update_redis_cache,
    dag=dag,
    doc_md="""
    ## Update Redis Cache

    Warms up Redis cache with embeddings for top items.
    Non-critical task - failures won't stop the pipeline.
    """,
)

# Define task dependencies
task_validate_data >> task_trigger_training >> task_wait_completion >> task_build_index >> task_deploy >> task_update_cache
