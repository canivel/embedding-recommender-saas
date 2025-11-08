"""
Data Quality Check DAG
Monitors data quality, freshness, and anomalies across all tenants.
Runs hourly to ensure data integrity.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.redis.hooks.redis import RedisHook
from datetime import datetime, timedelta
import logging

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

logger = logging.getLogger(__name__)

def check_data_completeness(**context):
    """
    Check for missing required fields in interaction data
    """
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

    # Query to check for incomplete records
    query = """
    SELECT
        tenant_id,
        COUNT(*) as total_records,
        SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as missing_user_id,
        SUM(CASE WHEN item_id IS NULL THEN 1 ELSE 0 END) as missing_item_id,
        SUM(CASE WHEN interaction_type IS NULL THEN 1 ELSE 0 END) as missing_interaction_type,
        SUM(CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END) as missing_timestamp
    FROM interactions
    WHERE created_at >= NOW() - INTERVAL '1 hour'
    GROUP BY tenant_id
    """

    results = postgres_hook.get_records(query)

    issues = []
    for row in results:
        tenant_id, total, missing_user, missing_item, missing_type, missing_ts = row

        if total == 0:
            logger.warning(f"No data received for tenant {tenant_id} in the last hour")
            issues.append({
                'tenant_id': tenant_id,
                'issue': 'no_data',
                'severity': 'medium'
            })

        missing_ratio = (missing_user + missing_item + missing_type + missing_ts) / (total * 4)
        if missing_ratio > 0.01:  # More than 1% missing data
            logger.error(f"Tenant {tenant_id} has {missing_ratio*100:.2f}% missing data")
            issues.append({
                'tenant_id': tenant_id,
                'issue': 'high_missing_data',
                'severity': 'high',
                'details': {
                    'total_records': total,
                    'missing_user_id': missing_user,
                    'missing_item_id': missing_item,
                    'missing_interaction_type': missing_type,
                    'missing_timestamp': missing_ts,
                }
            })

    if issues:
        logger.warning(f"Data completeness issues found: {len(issues)} tenants affected")
        # Store issues for alerting
        context['task_instance'].xcom_push(key='completeness_issues', value=issues)
    else:
        logger.info("Data completeness check passed for all tenants")

    return len(issues)

def check_data_freshness(**context):
    """
    Check if data is being ingested in a timely manner
    """
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

    # Query to check data freshness
    query = """
    SELECT
        tenant_id,
        MAX(timestamp) as latest_interaction,
        COUNT(*) as recent_count
    FROM interactions
    WHERE created_at >= NOW() - INTERVAL '1 hour'
    GROUP BY tenant_id
    """

    results = postgres_hook.get_records(query)

    stale_tenants = []
    now = datetime.now()

    for row in results:
        tenant_id, latest_interaction, recent_count = row

        if latest_interaction:
            data_age = (now - latest_interaction).total_seconds() / 3600  # hours

            if data_age > 24:  # No data in last 24 hours
                logger.error(f"Tenant {tenant_id} has stale data: {data_age:.1f} hours old")
                stale_tenants.append({
                    'tenant_id': tenant_id,
                    'issue': 'stale_data',
                    'severity': 'high',
                    'data_age_hours': data_age,
                    'recent_count': recent_count
                })
            elif data_age > 6:  # Warning for data older than 6 hours
                logger.warning(f"Tenant {tenant_id} has aging data: {data_age:.1f} hours old")
                stale_tenants.append({
                    'tenant_id': tenant_id,
                    'issue': 'aging_data',
                    'severity': 'medium',
                    'data_age_hours': data_age,
                    'recent_count': recent_count
                })

    # Check for active tenants with no recent data
    all_active_tenants_query = """
    SELECT tenant_id
    FROM tenants
    WHERE status = 'active'
    AND tenant_id NOT IN (
        SELECT DISTINCT tenant_id
        FROM interactions
        WHERE created_at >= NOW() - INTERVAL '1 hour'
    )
    """

    inactive_tenants = postgres_hook.get_records(all_active_tenants_query)

    for (tenant_id,) in inactive_tenants:
        logger.warning(f"Active tenant {tenant_id} has no recent data")
        stale_tenants.append({
            'tenant_id': tenant_id,
            'issue': 'no_recent_data',
            'severity': 'medium'
        })

    if stale_tenants:
        logger.warning(f"Data freshness issues: {len(stale_tenants)} tenants affected")
        context['task_instance'].xcom_push(key='freshness_issues', value=stale_tenants)
    else:
        logger.info("Data freshness check passed for all tenants")

    return len(stale_tenants)

def detect_anomalies(**context):
    """
    Detect statistical anomalies in data patterns
    """
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

    # Query for anomaly detection
    query = """
    WITH hourly_stats AS (
        SELECT
            tenant_id,
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as interaction_count,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT item_id) as unique_items
        FROM interactions
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY tenant_id, DATE_TRUNC('hour', created_at)
    ),
    stats AS (
        SELECT
            tenant_id,
            AVG(interaction_count) as avg_interactions,
            STDDEV(interaction_count) as stddev_interactions,
            AVG(unique_users) as avg_users,
            STDDEV(unique_users) as stddev_users
        FROM hourly_stats
        WHERE hour < DATE_TRUNC('hour', NOW())
        GROUP BY tenant_id
    ),
    current_hour AS (
        SELECT
            tenant_id,
            COUNT(*) as current_interactions,
            COUNT(DISTINCT user_id) as current_users,
            COUNT(DISTINCT item_id) as current_items
        FROM interactions
        WHERE created_at >= DATE_TRUNC('hour', NOW())
        GROUP BY tenant_id
    )
    SELECT
        s.tenant_id,
        s.avg_interactions,
        s.stddev_interactions,
        c.current_interactions,
        s.avg_users,
        s.stddev_users,
        c.current_users,
        c.current_items,
        -- Z-score for interactions
        CASE
            WHEN s.stddev_interactions > 0
            THEN (c.current_interactions - s.avg_interactions) / s.stddev_interactions
            ELSE 0
        END as interactions_zscore,
        -- Z-score for users
        CASE
            WHEN s.stddev_users > 0
            THEN (c.current_users - s.avg_users) / s.stddev_users
            ELSE 0
        END as users_zscore
    FROM stats s
    JOIN current_hour c ON s.tenant_id = c.tenant_id
    WHERE s.stddev_interactions IS NOT NULL
    """

    results = postgres_hook.get_records(query)

    anomalies = []

    for row in results:
        (tenant_id, avg_int, stddev_int, curr_int, avg_users, stddev_users,
         curr_users, curr_items, int_zscore, users_zscore) = row

        # Flag if Z-score is beyond 3 standard deviations
        if abs(int_zscore) > 3:
            severity = 'high' if abs(int_zscore) > 5 else 'medium'
            direction = 'spike' if int_zscore > 0 else 'drop'

            logger.warning(
                f"Anomaly detected for tenant {tenant_id}: "
                f"{direction} in interactions (Z-score: {int_zscore:.2f})"
            )

            anomalies.append({
                'tenant_id': tenant_id,
                'issue': f'interaction_{direction}',
                'severity': severity,
                'details': {
                    'current_interactions': curr_int,
                    'average_interactions': avg_int,
                    'zscore': float(int_zscore),
                    'current_users': curr_users,
                    'current_items': curr_items
                }
            })

        if abs(users_zscore) > 3:
            severity = 'medium'
            direction = 'spike' if users_zscore > 0 else 'drop'

            logger.warning(
                f"Anomaly detected for tenant {tenant_id}: "
                f"{direction} in unique users (Z-score: {users_zscore:.2f})"
            )

            anomalies.append({
                'tenant_id': tenant_id,
                'issue': f'user_{direction}',
                'severity': severity,
                'details': {
                    'current_users': curr_users,
                    'average_users': avg_users,
                    'zscore': float(users_zscore),
                }
            })

    if anomalies:
        logger.warning(f"Anomalies detected: {len(anomalies)} issues found")
        context['task_instance'].xcom_push(key='anomalies', value=anomalies)
    else:
        logger.info("No anomalies detected in current data")

    return len(anomalies)

def aggregate_and_alert(**context):
    """
    Aggregate all issues and send alerts if necessary
    """
    ti = context['task_instance']

    # Get all issues from previous tasks
    completeness_issues = ti.xcom_pull(key='completeness_issues', task_ids='check_data_completeness') or []
    freshness_issues = ti.xcom_pull(key='freshness_issues', task_ids='check_data_freshness') or []
    anomalies = ti.xcom_pull(key='anomalies', task_ids='check_anomalies') or []

    all_issues = completeness_issues + freshness_issues + anomalies

    if all_issues:
        # Count by severity
        high_severity = len([i for i in all_issues if i.get('severity') == 'high'])
        medium_severity = len([i for i in all_issues if i.get('severity') == 'medium'])

        logger.warning(
            f"Data quality check summary: {len(all_issues)} total issues "
            f"({high_severity} high, {medium_severity} medium)"
        )

        # In production, this would send alerts via PagerDuty, Slack, etc.
        if high_severity > 0:
            logger.error(f"HIGH SEVERITY ISSUES: {high_severity} critical data quality problems detected")
            # TODO: Send alert to on-call team

        # Store aggregated issues for reporting
        postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
        for issue in all_issues:
            insert_query = """
            INSERT INTO data_quality_issues (
                tenant_id, issue_type, severity, details, detected_at
            ) VALUES (%s, %s, %s, %s, NOW())
            """
            postgres_hook.run(
                insert_query,
                parameters=(
                    issue.get('tenant_id'),
                    issue.get('issue'),
                    issue.get('severity'),
                    str(issue.get('details', {}))
                )
            )
    else:
        logger.info("All data quality checks passed successfully")

    return len(all_issues)

with DAG(
    'data_quality_check',
    default_args=default_args,
    description='Hourly data quality monitoring across all tenants',
    schedule_interval='0 * * * *',  # Hourly at the top of the hour
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['monitoring', 'data-quality', 'production'],
) as dag:

    # Parallel quality checks
    check_completeness = PythonOperator(
        task_id='check_data_completeness',
        python_callable=check_data_completeness,
        provide_context=True,
    )

    check_freshness = PythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness,
        provide_context=True,
    )

    check_anomalies = PythonOperator(
        task_id='check_anomalies',
        python_callable=detect_anomalies,
        provide_context=True,
    )

    # Aggregate results and alert
    alert_task = PythonOperator(
        task_id='aggregate_and_alert',
        python_callable=aggregate_and_alert,
        provide_context=True,
    )

    # All checks run in parallel, then aggregate
    [check_completeness, check_freshness, check_anomalies] >> alert_task
