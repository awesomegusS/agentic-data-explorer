-- data/snowflake_setup.sql
-- Snowflake database and schema setup for Agentic Data Explorer

-- =============================================================================
-- STEP 1: CREATE DATABASE AND SCHEMAS
-- =============================================================================

-- Create main database
CREATE DATABASE IF NOT EXISTS retail_analytics
    COMMENT = 'Database for Agentic Data Explorer retail analytics project';

-- Create schemas for different data layers
USE DATABASE retail_analytics;

CREATE SCHEMA IF NOT EXISTS raw
    COMMENT = 'Raw data ingestion layer - unprocessed source data';

CREATE SCHEMA IF NOT EXISTS staging  
    COMMENT = 'Staging layer - cleaned and validated data';

CREATE SCHEMA IF NOT EXISTS analytics
    COMMENT = 'Analytics layer - business-ready dimensional model';

-- =============================================================================
-- STEP 2: CREATE RAW TABLES FOR DATA INGESTION
-- =============================================================================

USE SCHEMA retail_analytics.raw;

-- Raw sales transactions table
CREATE TABLE IF NOT EXISTS sales (
    transaction_id VARCHAR(50) NOT NULL,
    store_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    sale_date DATE NOT NULL,
    sale_timestamp TIMESTAMP_NTZ,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    customer_segment VARCHAR(50),
    payment_method VARCHAR(50),
    discount_applied DECIMAL(5,2) DEFAULT 0,
    sales_rep_id VARCHAR(20),
    -- Metadata columns
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file VARCHAR(255),
    CONSTRAINT pk_sales PRIMARY KEY (transaction_id)
)
COMMENT = 'Raw sales transaction data from source systems';

-- Raw stores table  
CREATE TABLE IF NOT EXISTS stores (
    store_id VARCHAR(20) NOT NULL,
    store_name VARCHAR(100) NOT NULL,
    store_location VARCHAR(200),
    store_region VARCHAR(50),
    store_size VARCHAR(20),
    opening_date DATE,
    -- Metadata columns
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file VARCHAR(255),
    CONSTRAINT pk_stores PRIMARY KEY (store_id)
)
COMMENT = 'Store master data';

-- Raw products table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_category VARCHAR(100),
    brand VARCHAR(100),
    cost_price DECIMAL(10,2),
    -- Metadata columns  
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file VARCHAR(255),
    CONSTRAINT pk_products PRIMARY KEY (product_id)
)
COMMENT = 'Product master data';

-- =============================================================================
-- STEP 3: CREATE DATA QUALITY MONITORING VIEW
-- =============================================================================

CREATE OR REPLACE VIEW data_quality_summary AS
SELECT 
    'sales' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN transaction_id IS NULL THEN 1 END) as null_transaction_ids,
    COUNT(CASE WHEN quantity <= 0 THEN 1 END) as invalid_quantities,
    COUNT(CASE WHEN unit_price <= 0 THEN 1 END) as invalid_prices,
    COUNT(CASE WHEN total_amount != quantity * unit_price THEN 1 END) as calculation_errors,
    MIN(sale_date) as earliest_date,
    MAX(sale_date) as latest_date,
    SUM(total_amount) as total_revenue
FROM sales

UNION ALL

SELECT 
    'stores' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN store_id IS NULL THEN 1 END) as null_store_ids,
    0 as invalid_quantities,
    0 as invalid_prices, 
    0 as calculation_errors,
    MIN(opening_date) as earliest_date,
    MAX(opening_date) as latest_date,
    0 as total_revenue
FROM stores

UNION ALL

SELECT 
    'products' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN product_id IS NULL THEN 1 END) as null_product_ids,
    0 as invalid_quantities,
    COUNT(CASE WHEN cost_price <= 0 THEN 1 END) as invalid_prices,
    0 as calculation_errors,
    NULL as earliest_date,
    NULL as latest_date,
    0 as total_revenue  
FROM products;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check table creation
SHOW TABLES IN SCHEMA retail_analytics.raw;

-- Test data quality view (will be empty until data is loaded)
SELECT * FROM retail_analytics.raw.data_quality_summary;

COMMENT ON DATABASE retail_analytics IS 
    'Database setup complete. Ready for data loading and dbt transformations.';