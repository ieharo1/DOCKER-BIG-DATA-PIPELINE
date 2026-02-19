import os
import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoDataExtractor:
    """Extract cryptocurrency data from CoinGecko API"""

    def __init__(self, base_url: str = None, coins: str = None, currency: str = None):
        self.base_url = base_url or os.getenv(
            "API_BASE_URL", "https://api.coingecko.com/api/v3"
        )
        self.coins = (coins or os.getenv("API_COINS", "bitcoin,ethereum")).split(",")
        self.currency = currency or os.getenv("API_CURRENCY", "usd")
        self.batch_size = int(os.getenv("EXTRACTION_BATCH_SIZE", "100"))
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 5

    def validate_response(self, response: requests.Response) -> bool:
        """Validate API response status code"""
        if response.status_code == 200:
            return True
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded, waiting for retry...")
            time.sleep(self.retry_delay * 2)
            return False
        elif response.status_code == 404:
            logger.error("API endpoint not found")
            return False
        else:
            logger.error(f"API error: {response.status_code}")
            return False

    def fetch_with_retry(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching data from: {url} (attempt {attempt + 1})")
                response = requests.get(url, params=params, timeout=self.timeout)

                if self.validate_response(response):
                    return response.json()
                elif attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                return None

        logger.error(f"Failed after {self.max_retries} attempts")
        return None

    def extract_market_data(self) -> List[Dict[str, Any]]:
        """Extract cryptocurrency market data from CoinGecko"""
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": self.currency,
            "ids": ",".join(self.coins),
            "order": "market_cap_desc",
            "per_page": len(self.coins),
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d",
        }

        data = self.fetch_with_retry(url, params)

        if not data:
            logger.error("Failed to extract market data")
            return []

        logger.info(f"Successfully extracted {len(data)} cryptocurrency records")
        return data

    def extract_coin_details(self, coin_id: str) -> Optional[Dict]:
        """Extract detailed information for a specific coin"""
        url = f"{self.base_url}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        }

        data = self.fetch_with_retry(url, params)

        if data:
            logger.info(f"Successfully extracted details for {coin_id}")

        return data

    def enrich_data(self, market_data: List[Dict]) -> List[Dict]:
        """Enrich market data with additional metadata"""
        enriched_data = []

        for coin in market_data:
            enriched_coin = {
                "coin_id": coin.get("id"),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "current_price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "total_volume": coin.get("total_volume"),
                "high_24h": coin.get("high_24h"),
                "low_24h": coin.get("low_24h"),
                "price_change_24h": coin.get("price_change_24h"),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                "market_cap_change_24h": coin.get("market_cap_change_24h"),
                "market_cap_change_percentage_24h": coin.get(
                    "market_cap_change_percentage_24h"
                ),
                "circulating_supply": coin.get("circulating_supply"),
                "total_supply": coin.get("total_supply"),
                "max_supply": coin.get("max_supply"),
                "ath": coin.get("ath"),
                "ath_change_percentage": coin.get("ath_change_percentage"),
                "ath_date": coin.get("ath_date"),
                "atl": coin.get("atl"),
                "atl_change_percentage": coin.get("atl_change_percentage"),
                "atl_date": coin.get("atl_date"),
                "last_updated": coin.get("last_updated"),
                "image": coin.get("image"),
                "extraction_date": datetime.now().strftime("%Y-%m-%d"),
                "extraction_timestamp": datetime.now().isoformat(),
            }
            enriched_data.append(enriched_coin)

        return enriched_data

    def save_raw_data(self, data: List[Dict], output_path: str) -> bool:
        """Save extracted data to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Raw data saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
            return False

    def extract(self, save_path: str = None) -> Dict[str, Any]:
        """Main extraction method"""
        logger.info("=" * 60)
        logger.info("Starting data extraction from CoinGecko API")
        logger.info("=" * 60)

        start_time = datetime.now()

        market_data = self.extract_market_data()

        if not market_data:
            return {
                "success": False,
                "error": "Failed to extract data from API",
                "records_extracted": 0,
                "duration_seconds": 0,
            }

        enriched_data = self.enrich_data(market_data)

        if save_path:
            self.save_raw_data(enriched_data, save_path)

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "success": True,
            "records_extracted": len(enriched_data),
            "data": enriched_data,
            "duration_seconds": duration,
            "source": "coingecko",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extraction_timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Extraction completed in {duration:.2f} seconds")
        logger.info(f"Records extracted: {len(enriched_data)}")

        return result


def run_extraction(**context):
    """Airflow callable extraction function"""
    execution_date = context.get("ds", datetime.now().strftime("%Y-%m-%d"))

    extractor = CryptoDataExtractor()

    result = extractor.extract()

    if result["success"]:
        ti = context["ti"]
        ti.xcom_push(key="extracted_data", value=result["data"])
        ti.xcom_push(
            key="extraction_metadata",
            value={
                "records_extracted": result["records_extracted"],
                "duration_seconds": result["duration_seconds"],
                "extraction_date": result["extraction_date"],
            },
        )

    return result


if __name__ == "__main__":
    extractor = CryptoDataExtractor()
    result = extractor.extract()
    print(json.dumps(result, indent=2, default=str))
