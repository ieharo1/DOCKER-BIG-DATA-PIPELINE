import os
import logging
import json
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load data into PostgreSQL and MinIO"""

    def __init__(self):
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "pipeline_warehouse"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres_secure_2026"),
        }

        self.minio_config = {
            "endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
            "access_key": os.getenv("MINIO_ROOT_USER", "minioadmin"),
            "secret_key": os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_secure_2026"),
            "bucket": os.getenv("MINIO_BUCKET", "pipeline-raw"),
        }

        self.minio_client = None

    def get_db_connection(self):
        """Create PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info("Database connection established")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_minio_client(self):
        """Create MinIO client"""
        try:
            from minio import Minio

            if not self.minio_client:
                self.minio_client = Minio(
                    self.minio_config["endpoint"],
                    access_key=self.minio_config["access_key"],
                    secret_key=self.minio_config["secret_key"],
                    secure=False,
                )

            return self.minio_client
        except Exception as e:
            logger.error(f"Failed to create MinIO client: {e}")
            return None

    def ensure_bucket_exists(self) -> bool:
        """Ensure MinIO bucket exists"""
        try:
            client = self.get_minio_client()
            if not client:
                return False

            if not client.bucket_exists(self.minio_config["bucket"]):
                client.make_bucket(self.minio_config["bucket"])
                logger.info(f"Created bucket: {self.minio_config['bucket']}")
            else:
                logger.info(f"Bucket already exists: {self.minio_config['bucket']}")

            return True
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            return False

    def upload_to_minio(self, data: Any, object_name: str) -> bool:
        """Upload data to MinIO"""
        try:
            client = self.get_minio_client()
            if not client:
                return False

            self.ensure_bucket_exists()

            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data, indent=2, default=str).encode("utf-8")
            elif isinstance(data, str):
                data = data.encode("utf-8")

            data_length = len(data)
            data_stream = BytesIO(data)

            client.put_object(
                self.minio_config["bucket"],
                object_name,
                data_stream,
                length=data_length,
            )

            logger.info(f"Uploaded to MinIO: {object_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            return False

    def load_crypto_prices(self, data: List[Dict]) -> int:
        """Load cryptocurrency prices into PostgreSQL"""
        conn = None
        records_loaded = 0

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO crypto_prices (
                    coin_id, symbol, name, current_price, market_cap, 
                    market_cap_rank, total_volume, high_24h, low_24h,
                    price_change_24h, price_change_percentage_24h,
                    market_cap_change_24h, market_cap_change_percentage_24h,
                    circulating_supply, total_supply, max_supply,
                    ath, ath_change_percentage, ath_date,
                    atl, atl_change_percentage, atl_date,
                    last_updated, extraction_date, extraction_timestamp
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """

            values = []
            for record in data:
                values.append(
                    (
                        record.get("coin_id"),
                        record.get("symbol"),
                        record.get("name"),
                        record.get("current_price", 0),
                        record.get("market_cap"),
                        record.get("market_cap_rank"),
                        record.get("total_volume"),
                        record.get("high_24h"),
                        record.get("low_24h"),
                        record.get("price_change_24h"),
                        record.get("price_change_percentage_24h"),
                        record.get("market_cap_change_24h"),
                        record.get("market_cap_change_percentage_24h"),
                        record.get("circulating_supply"),
                        record.get("total_supply"),
                        record.get("max_supply"),
                        record.get("ath"),
                        record.get("ath_change_percentage"),
                        record.get("ath_date"),
                        record.get("atl"),
                        record.get("atl_change_percentage"),
                        record.get("atl_date"),
                        record.get("last_updated"),
                        record.get("extraction_date"),
                        record.get("extraction_timestamp"),
                    )
                )

            if values:
                execute_values(cursor, insert_query, values)
                conn.commit()
                records_loaded = len(values)
                logger.info(f"Loaded {records_loaded} crypto price records")

        except Exception as e:
            logger.error(f"Failed to load crypto prices: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

        return records_loaded

    def load_price_aggregates(self, data: List[Dict]) -> int:
        """Load price aggregates into PostgreSQL"""
        conn = None
        records_loaded = 0

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO price_aggregates (
                    coin_id, symbol, name, extraction_date,
                    avg_price, min_price, max_price, price_range,
                    avg_market_cap, avg_volume, volatility_percentage
                ) VALUES %s
                ON CONFLICT (coin_id, extraction_date) DO UPDATE
                SET avg_price = EXCLUDED.avg_price,
                    min_price = EXCLUDED.min_price,
                    max_price = EXCLUDED.max_price,
                    price_range = EXCLUDED.price_range,
                    avg_market_cap = EXCLUDED.avg_market_cap,
                    avg_volume = EXCLUDED.avg_volume,
                    volatility_percentage = EXCLUDED.volatility_percentage
            """

            values = []
            for record in data:
                values.append(
                    (
                        record.get("coin_id"),
                        record.get("symbol"),
                        record.get("name"),
                        record.get("extraction_date"),
                        record.get("avg_price", 0),
                        record.get("min_price", 0),
                        record.get("max_price", 0),
                        record.get("price_range", 0),
                        record.get("avg_market_cap", 0),
                        record.get("avg_volume", 0),
                        record.get("volatility_percentage", 0),
                    )
                )

            if values:
                execute_values(cursor, insert_query, values)
                conn.commit()
                records_loaded = len(values)
                logger.info(f"Loaded {records_loaded} aggregate records")

        except Exception as e:
            logger.error(f"Failed to load aggregates: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

        return records_loaded

    def log_pipeline_execution(
        self,
        dag_id: str,
        task_id: str,
        execution_date: str,
        status: str,
        records_extracted: int = 0,
        records_transformed: int = 0,
        records_loaded: int = 0,
        error_message: str = None,
    ) -> bool:
        """Log pipeline execution to database"""
        conn = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO pipeline_logs (
                    dag_id, task_id, execution_date, status,
                    records_extracted, records_transformed, records_loaded,
                    error_message, end_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """

            cursor.execute(
                insert_query,
                (
                    dag_id,
                    task_id,
                    execution_date,
                    status,
                    records_extracted,
                    records_transformed,
                    records_loaded,
                    error_message,
                ),
            )

            conn.commit()
            logger.info(f"Pipeline execution logged: {dag_id}/{task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log pipeline execution: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def load(
        self,
        transformed_data: List[Dict],
        aggregate_data: List[Dict],
        execution_date: str,
    ) -> Dict[str, Any]:
        """Main loading method"""
        logger.info("=" * 60)
        logger.info("Starting data load")
        logger.info("=" * 60)

        start_time = datetime.now()

        records_loaded = 0

        if transformed_data:
            records_loaded += self.load_crypto_prices(transformed_data)

            today = datetime.now()
            object_name = f"raw/{today.strftime('%Y')}/{today.strftime('%m')}/{today.strftime('%d')}/crypto_prices_{today.strftime('%Y%m%d_%H%M%S')}.json"
            self.upload_to_minio(transformed_data, object_name)

        if aggregate_data:
            records_loaded += self.load_price_aggregates(aggregate_data)

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "success": True,
            "records_loaded": records_loaded,
            "duration_seconds": duration,
            "execution_date": execution_date,
        }

        logger.info(f"Load completed in {duration:.2f} seconds")
        logger.info(f"Records loaded: {records_loaded}")

        return result


def run_load(**context):
    """Airflow callable load function"""
    ti = context["ti"]

    transformed_data = ti.xcom_pull(key="transformed_data", task_ids="transform")
    aggregate_data = ti.xcom_pull(key="aggregate_data", task_ids="transform")

    extraction_metadata = ti.xcom_pull(key="extraction_metadata", task_ids="extract")
    transformation_metadata = ti.xcom_pull(
        key="transformation_metadata", task_ids="transform"
    )

    execution_date = context.get("ds", datetime.now().strftime("%Y-%m-%d"))

    loader = DataLoader()
    result = loader.load(transformed_data or [], aggregate_data or [], execution_date)

    if result["success"]:
        loader.log_pipeline_execution(
            dag_id=context.get("dag").dag_id,
            task_id="load_db",
            execution_date=execution_date,
            status="success",
            records_extracted=extraction_metadata.get("records_extracted", 0)
            if extraction_metadata
            else 0,
            records_transformed=transformation_metadata.get("records_transformed", 0)
            if transformation_metadata
            else 0,
            records_loaded=result["records_loaded"],
        )

        ti.xcom_push(
            key="load_metadata",
            value={
                "records_loaded": result["records_loaded"],
                "duration_seconds": result["duration_seconds"],
            },
        )
    else:
        loader.log_pipeline_execution(
            dag_id=context.get("dag").dag_id,
            task_id="load_db",
            execution_date=execution_date,
            status="failed",
            error_message=result.get("error", "Unknown error"),
        )

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python load.py <input_json_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = json.load(f)

    loader = DataLoader()
    result = loader.load(data, [], datetime.now().strftime("%Y-%m-%d"))
    print(json.dumps(result, indent=2, default=str))
