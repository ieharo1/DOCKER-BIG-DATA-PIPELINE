"""
BIG DATA PIPELINE LAB - Crypto Data Pipeline DAG

This DAG orchestrates the complete ETL pipeline:
1. Extract: Fetches cryptocurrency data from CoinGecko API
2. Store Raw: Saves raw data to MinIO (Data Lake)
3. Transform: Cleans, normalizes and enriches the data
4. Load: Stores transformed data in PostgreSQL (Data Warehouse)
"""

import os
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowFailException

import sys

sys.path.insert(0, "/opt/airflow/scripts")

from extract import run_extraction
from transform import run_transformation
from load import run_load

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

default_args = {
    "owner": "Isaac Haro",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "execution_timeout": timedelta(minutes=30),
    "start_date": datetime(2026, 1, 1),
}


def extract_task(**context):
    """Extract task - fetches data from CoinGecko API"""
    logger.info("=" * 60)
    logger.info("TASK: EXTRACT - Starting data extraction")
    logger.info("=" * 60)

    try:
        result = run_extraction(**context)

        if not result.get("success"):
            raise AirflowFailException(f"Extraction failed: {result.get('error')}")

        logger.info(f"Extraction completed: {result.get('records_extracted')} records")
        return result

    except Exception as e:
        logger.error(f"Extraction task failed: {e}")
        raise


def store_raw_task(**context):
    """Store raw data to MinIO"""
    logger.info("=" * 60)
    logger.info("TASK: STORE_RAW - Saving raw data to MinIO")
    logger.info("=" * 60)

    try:
        ti = context["ti"]
        extracted_data = ti.xcom_pull(key="extracted_data", task_ids="extract")

        if not extracted_data:
            logger.warning("No extracted data found, skipping raw storage")
            return {"success": True, "skipped": True}

        from minio import Minio
        import json

        minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_secure_2026"),
            secure=False,
        )

        bucket_name = os.getenv("MINIO_BUCKET", "pipeline-raw")

        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        today = datetime.now()
        object_name = f"raw/{today.strftime('%Y')}/{today.strftime('%m')}/{today.strftime('%d')}/crypto_prices_{today.strftime('%Y%m%d_%H%M%S')}.json"

        data_json = json.dumps(extracted_data, indent=2, default=str).encode("utf-8")

        minio_client.put_object(
            bucket_name, object_name, data_json, length=len(data_json)
        )

        logger.info(f"Raw data stored: {object_name}")

        return {"success": True, "object_name": object_name}

    except Exception as e:
        logger.error(f"Store raw task failed: {e}")
        raise


def transform_task(**context):
    """Transform task - cleans and enriches data"""
    logger.info("=" * 60)
    logger.info("TASK: TRANSFORM - Starting data transformation")
    logger.info("=" * 60)

    try:
        result = run_transformation(**context)

        if not result.get("success"):
            raise AirflowFailException(f"Transformation failed: {result.get('error')}")

        logger.info(
            f"Transformation completed: {result.get('records_transformed')} records"
        )
        return result

    except Exception as e:
        logger.error(f"Transformation task failed: {e}")
        raise


def load_task(**context):
    """Load task - stores data in PostgreSQL"""
    logger.info("=" * 60)
    logger.info("TASK: LOAD - Starting data load to PostgreSQL")
    logger.info("=" * 60)

    try:
        result = run_load(**context)

        if not result.get("success"):
            raise AirflowFailException(f"Load failed: {result.get('error')}")

        logger.info(f"Load completed: {result.get('records_loaded')} records")
        return result

    except Exception as e:
        logger.error(f"Load task failed: {e}")
        raise


def log_success_task(**context):
    """Log successful pipeline completion"""
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    ti = context["ti"]

    extraction_meta = ti.xcom_pull(key="extraction_metadata", task_ids="extract")
    transformation_meta = ti.xcom_pull(
        key="transformation_metadata", task_ids="transform"
    )
    load_meta = ti.xcom_pull(key="load_metadata", task_ids="load_db")

    logger.info(f"Extraction: {extraction_meta}")
    logger.info(f"Transformation: {transformation_meta}")
    logger.info(f"Load: {load_meta}")


with DAG(
    dag_id="crypto_data_pipeline",
    default_args=default_args,
    description="Big Data Pipeline - Crypto Data ETL",
    schedule_interval="@hourly",
    catchup=False,
    max_active_runs=1,
    max_active_tasks=4,
    tags=["etl", "crypto", "pipeline", "big-data"],
    doc_md=__doc__,
) as dag:
    start = EmptyOperator(task_id="start", doc_md="Pipeline start")

    end = EmptyOperator(
        task_id="end", doc_md="Pipeline end", trigger_rule=TriggerRule.ALL_SUCCESS
    )

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=15),
        doc_md="Extract cryptocurrency data from CoinGecko API",
    )

    store_raw = PythonOperator(
        task_id="store_raw",
        python_callable=store_raw_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=10),
        doc_md="Store raw data to MinIO Data Lake",
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=15),
        doc_md="Transform and clean the extracted data",
    )

    load_db = PythonOperator(
        task_id="load_db",
        python_callable=load_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=15),
        doc_md="Load transformed data to PostgreSQL",
    )

    log_success = PythonOperator(
        task_id="log_success",
        python_callable=log_success_task,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_SUCCESS,
        doc_md="Log pipeline success",
    )

    start >> extract >> store_raw >> transform >> load_db >> log_success >> end
