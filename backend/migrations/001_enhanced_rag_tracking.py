"""
Database migration script: Add enhanced tracking fields to analysis_cache table.

This migration adds:
- Price tracking fields (price, previous_close, day_high, day_low, volume)
- Technical indicator fields (RSI, MACD, Bollinger Bands)
- Prediction tracking fields (prediction_text, prediction_direction, confidence)
- Historical context fields (risk_factors_json, key_insights_json)

To run this migration:
1. Connect to MySQL database
2. Execute the SQL statements below
"""

SQL_MIGRATION = """
-- Add price tracking fields
ALTER TABLE analysis_cache
ADD COLUMN price FLOAT DEFAULT NULL AFTER article_count,
ADD COLUMN previous_close FLOAT DEFAULT NULL AFTER price,
ADD COLUMN day_high FLOAT DEFAULT NULL AFTER previous_close,
ADD COLUMN day_low FLOAT DEFAULT NULL AFTER day_high,
ADD COLUMN volume INT DEFAULT NULL AFTER day_low;

-- Add technical indicator fields (RSI)
ALTER TABLE analysis_cache
ADD COLUMN rsi FLOAT DEFAULT NULL AFTER volume,
ADD COLUMN rsi_signal VARCHAR(20) DEFAULT NULL AFTER rsi;

-- Add MACD fields
ALTER TABLE analysis_cache
ADD COLUMN macd FLOAT DEFAULT NULL AFTER rsi_signal,
ADD COLUMN macd_signal FLOAT DEFAULT NULL AFTER macd,
ADD COLUMN macd_histogram FLOAT DEFAULT NULL AFTER macd_signal,
ADD COLUMN macd_trend VARCHAR(20) DEFAULT NULL AFTER macd_histogram;

-- Add Bollinger Bands fields
ALTER TABLE analysis_cache
ADD COLUMN bb_upper FLOAT DEFAULT NULL AFTER macd_trend,
ADD COLUMN bb_middle FLOAT DEFAULT NULL AFTER bb_upper,
ADD COLUMN bb_lower FLOAT DEFAULT NULL AFTER bb_middle,
ADD COLUMN bb_position VARCHAR(50) DEFAULT NULL AFTER bb_lower;

-- Add prediction tracking fields
ALTER TABLE analysis_cache
ADD COLUMN prediction_text TEXT DEFAULT NULL AFTER bb_position,
ADD COLUMN prediction_direction VARCHAR(20) DEFAULT NULL AFTER prediction_text,
ADD COLUMN confidence FLOAT DEFAULT NULL AFTER prediction_direction;

-- Add historical context fields
ALTER TABLE analysis_cache
ADD COLUMN risk_factors_json JSON DEFAULT NULL AFTER confidence,
ADD COLUMN key_insights_json JSON DEFAULT NULL AFTER risk_factors_json;

-- Create technical_indicator_history table
CREATE TABLE IF NOT EXISTS technical_indicator_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    
    -- OHLCV Data
    open_price FLOAT DEFAULT NULL,
    high_price FLOAT DEFAULT NULL,
    low_price FLOAT DEFAULT NULL,
    close_price FLOAT DEFAULT NULL,
    volume INT DEFAULT NULL,
    
    -- Technical Indicators
    rsi_14 FLOAT DEFAULT NULL,
    rsi_signal VARCHAR(20) DEFAULT NULL,
    macd FLOAT DEFAULT NULL,
    macd_signal FLOAT DEFAULT NULL,
    macd_histogram FLOAT DEFAULT NULL,
    bb_upper FLOAT DEFAULT NULL,
    bb_middle FLOAT DEFAULT NULL,
    bb_lower FLOAT DEFAULT NULL,
    bb_width FLOAT DEFAULT NULL,
    
    -- Indexes for fast queries
    INDEX idx_ticker (ticker),
    INDEX idx_timestamp (timestamp),
    INDEX idx_ticker_timestamp (ticker, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Python script to run migration
if __name__ == "__main__":
    import mysql.connector
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Connect to database
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "stock_analysis")
    )
    
    cursor = conn.cursor()
    
    print("🔄 Running database migration...")
    
    # Execute migration statements
    for statement in SQL_MIGRATION.strip().split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                print(f"✅ Executed: {statement[:50]}...")
            except mysql.connector.Error as err:
                if "Duplicate column name" in str(err):
                    print(f"⚠️  Column already exists, skipping")
                elif "Table 'technical_indicator_history' already exists" in str(err):
                    print(f"⚠️  Table already exists, skipping")
                else:
                    print(f"❌ Error: {err}")
                    raise
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Migration completed successfully!")
