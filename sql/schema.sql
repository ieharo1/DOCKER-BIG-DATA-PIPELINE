-- =============================================================================
-- BIG DATA PIPELINE LAB - PostgreSQL Schema
-- =============================================================================

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Table: crypto_prices
-- Stores cryptocurrency price data from the API
-- =============================================================================
CREATE TABLE IF NOT EXISTS crypto_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    coin_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    current_price DECIMAL(20, 8) NOT NULL,
    market_cap BIGINT,
    market_cap_rank INTEGER,
    total_volume BIGINT,
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    price_change_24h DECIMAL(20, 8),
    price_change_percentage_24h DECIMAL(10, 4),
    market_cap_change_24h BIGINT,
    market_cap_change_percentage_24h DECIMAL(10, 4),
    circulating_supply DECIMAL(20, 8),
    total_supply DECIMAL(20, 8),
    max_supply DECIMAL(20, 8),
    ath DECIMAL(20, 8),
    ath_change_percentage DECIMAL(10, 4),
    ath_date TIMESTAMP,
    atl DECIMAL(20, 8),
    atl_change_percentage DECIMAL(10, 4),
    atl_date TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_date DATE NOT NULL,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient date-based queries
CREATE INDEX idx_crypto_prices_date ON crypto_prices(extraction_date);
CREATE INDEX idx_crypto_prices_coin_id ON crypto_prices(coin_id);
CREATE INDEX idx_crypto_prices_symbol ON crypto_prices(symbol);
CREATE INDEX idx_crypto_prices_updated ON crypto_prices(last_updated);

-- =============================================================================
-- Table: price_aggregates
-- Stores aggregated metrics per day per cryptocurrency
-- =============================================================================
CREATE TABLE IF NOT EXISTS price_aggregates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    coin_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    extraction_date DATE NOT NULL,
    avg_price DECIMAL(20, 8),
    min_price DECIMAL(20, 8),
    max_price DECIMAL(20, 8),
    price_range DECIMAL(20, 8),
    avg_market_cap BIGINT,
    avg_volume BIGINT,
    total_transactions INTEGER,
    volatility_percentage DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin_id, extraction_date)
);

-- Index for aggregate queries
CREATE INDEX idx_price_aggregates_date ON price_aggregates(extraction_date);
CREATE INDEX idx_price_aggregates_coin ON price_aggregates(coin_id);

-- =============================================================================
-- Table: pipeline_logs
-- Tracks pipeline execution history
-- =============================================================================
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dag_id VARCHAR(100) NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    execution_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    records_extracted INTEGER DEFAULT 0,
    records_transformed INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);

-- Index for pipeline monitoring
CREATE INDEX idx_pipeline_logs_dag ON pipeline_logs(dag_id, execution_date DESC);
CREATE INDEX idx_pipeline_logs_status ON pipeline_logs(status);

-- =============================================================================
-- Table: minio_file_tracking
-- Tracks files stored in MinIO
-- =============================================================================
CREATE TABLE IF NOT EXISTS minio_file_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path VARCHAR(500) NOT NULL,
    bucket_name VARCHAR(100) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    extraction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT FALSE,
    UNIQUE(bucket_name, file_path)
);

-- Index for file tracking
CREATE INDEX idx_minio_files_date ON minio_file_tracking(extraction_date);
CREATE INDEX idx_minio_files_processed ON minio_file_tracking(is_processed);

-- =============================================================================
-- Create insert trigger for timestamp updates
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_crypto_prices_timestamp
    BEFORE UPDATE ON crypto_prices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Grant necessary permissions
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO airflow;
