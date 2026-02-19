import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform and clean cryptocurrency data"""

    def __init__(self):
        self.null_threshold = 0.5

    def clean_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove or fill null values"""
        initial_rows = len(df)

        for col in df.columns:
            null_percentage = df[col].isnull().sum() / len(df)

            if null_percentage > self.null_threshold:
                logger.warning(
                    f"Column {col} has {null_percentage:.1%} nulls, dropping"
                )
                df = df.drop(columns=[col])
            else:
                if df[col].dtype in ["float64", "int64"]:
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna("")

        logger.info(f"Cleaned nulls: {initial_rows} -> {len(df)} rows")
        return df

    def convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert data types for consistency"""
        numeric_columns = [
            "current_price",
            "market_cap",
            "total_volume",
            "high_24h",
            "low_24h",
            "price_change_24h",
            "price_change_percentage_24h",
            "circulating_supply",
            "total_supply",
            "max_supply",
            "ath",
            "atl",
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        if "extraction_date" in df.columns:
            df["extraction_date"] = pd.to_datetime(
                df["extraction_date"], errors="coerce"
            )

        if "ath_date" in df.columns:
            df["ath_date"] = pd.to_datetime(
                df["ath_date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        if "atl_date" in df.columns:
            df["atl_date"] = pd.to_datetime(
                df["atl_date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        if "last_updated" in df.columns:
            df["last_updated"] = pd.to_datetime(
                df["last_updated"], errors="coerce"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        logger.info("Data types converted successfully")
        return df

    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize data formats"""
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].str.upper().str.strip()

        if "name" in df.columns:
            df["name"] = df["name"].str.strip()

        if "coin_id" in df.columns:
            df["coin_id"] = df["coin_id"].str.strip().str.lower()

        if "image" in df.columns:
            df = df.drop(columns=["image"])

        logger.info("Data normalized successfully")
        return df

    def add_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated/enriched fields"""
        if "high_24h" in df.columns and "low_24h" in df.columns:
            df["price_range_24h"] = df["high_24h"] - df["low_24h"]

        if "ath" in df.columns and "current_price" in df.columns:
            df["distance_from_ath_percentage"] = (
                (df["ath"] - df["current_price"]) / df["ath"] * 100
            ).fillna(0)

        if "atl" in df.columns and "current_price" in df.columns:
            df["distance_from_atl_percentage"] = (
                (df["current_price"] - df["atl"]) / df["atl"] * 100
            ).fillna(0)

        if "circulating_supply" in df.columns and "total_supply" in df.columns:
            df["supply_ratio"] = (
                df["circulating_supply"] / df["total_supply"].replace(0, 1)
            ).fillna(0)

        if "market_cap" in df.columns and "total_volume" in df.columns:
            df["volume_to_market_cap_ratio"] = (
                df["total_volume"] / df["market_cap"].replace(0, 1)
            ).fillna(0)

        logger.info("Calculated fields added successfully")
        return df

    def generate_aggregates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate daily aggregates per coin"""
        if "extraction_date" not in df.columns:
            logger.warning("No extraction_date column found, skipping aggregation")
            return pd.DataFrame()

        aggregates = (
            df.groupby(["coin_id", "symbol", "name", "extraction_date"])
            .agg(
                {
                    "current_price": ["mean", "min", "max"],
                    "market_cap": "mean",
                    "total_volume": "mean",
                    "price_change_percentage_24h": "mean",
                    "circulating_supply": "mean",
                }
            )
            .reset_index()
        )

        aggregates.columns = [
            "coin_id",
            "symbol",
            "name",
            "extraction_date",
            "avg_price",
            "min_price",
            "max_price",
            "avg_market_cap",
            "avg_volume",
            "avg_price_change_pct",
            "avg_circulating_supply",
        ]

        aggregates["price_range"] = aggregates["max_price"] - aggregates["min_price"]

        aggregates["volatility_percentage"] = (
            (aggregates["price_range"] / aggregates["avg_price"] * 100)
            .replace([float("inf"), -float("inf")], 0)
            .fillna(0)
        )

        logger.info(f"Generated {len(aggregates)} aggregate records")
        return aggregates

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate transformed data quality"""
        if df.empty:
            logger.error("DataFrame is empty after transformation")
            return False

        required_columns = ["coin_id", "symbol", "name", "current_price"]

        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Required column {col} missing")
                return False

        if df["current_price"].isnull().all():
            logger.error("All current_price values are null")
            return False

        logger.info("Data validation passed")
        return True

    def transform(self, data: List[Dict]) -> Dict[str, Any]:
        """Main transformation method"""
        logger.info("=" * 60)
        logger.info("Starting data transformation")
        logger.info("=" * 60)

        start_time = datetime.now()

        df = pd.DataFrame(data)

        if df.empty:
            return {
                "success": False,
                "error": "No data to transform",
                "records_transformed": 0,
            }

        logger.info(f"Input records: {len(df)}")

        df = self.clean_nulls(df)
        df = self.convert_types(df)
        df = self.normalize_data(df)
        df = self.add_calculated_fields(df)

        if not self.validate_data(df):
            return {
                "success": False,
                "error": "Data validation failed",
                "records_transformed": 0,
            }

        aggregates = self.generate_aggregates(df)

        # Ensure values are JSON-serializable for Airflow XCom.
        transformed_data = json.loads(json.dumps(df.to_dict("records"), default=str))

        if not aggregates.empty:
            aggregate_data = json.loads(
                json.dumps(aggregates.to_dict("records"), default=str)
            )
        else:
            aggregate_data = []

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "success": True,
            "records_transformed": len(transformed_data),
            "records_aggregated": len(aggregate_data),
            "transformed_data": transformed_data,
            "aggregate_data": aggregate_data,
            "duration_seconds": duration,
        }

        logger.info(f"Transformation completed in {duration:.2f} seconds")
        logger.info(f"Records transformed: {len(transformed_data)}")

        return result

    def save_transformed_data(self, data: List[Dict], output_path: str) -> bool:
        """Save transformed data to JSON file"""
        try:
            import os

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Transformed data saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save transformed data: {e}")
            return False


def run_transformation(**context):
    """Airflow callable transformation function"""
    ti = context["ti"]

    extracted_data = ti.xcom_pull(key="extracted_data", task_ids="extract")

    if not extracted_data:
        return {
            "success": False,
            "error": "No extracted data found",
            "records_transformed": 0,
        }

    transformer = DataTransformer()
    result = transformer.transform(extracted_data)

    if result["success"]:
        ti.xcom_push(key="transformed_data", value=result["transformed_data"])
        ti.xcom_push(key="aggregate_data", value=result["aggregate_data"])
        ti.xcom_push(
            key="transformation_metadata",
            value={
                "records_transformed": result["records_transformed"],
                "records_aggregated": result["records_aggregated"],
                "duration_seconds": result["duration_seconds"],
            },
        )

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transform.py <input_json_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = json.load(f)

    transformer = DataTransformer()
    result = transformer.transform(data)
    print(json.dumps(result, indent=2, default=str))
