 -- Phase 6: Load to MySQL
-- Script 04: Verify data load

USE automated_data_quality_etl;

-- Check total rows loaded
SELECT COUNT(*) AS total_rows
FROM online_retail_feature_engineered;

-- Preview first 10 records
SELECT *
FROM online_retail_feature_engineered
LIMIT 10;

-- Check table structure
DESCRIBE online_retail_feature_engineered;

-- Check date range
SELECT 
    MIN(invoice_date) AS earliest_invoice_date,
    MAX(invoice_date) AS latest_invoice_date
FROM online_retail_feature_engineered;

-- Check countries loaded
SELECT 
    country,
    COUNT(*) AS total_records
FROM online_retail_feature_engineered
GROUP BY country
ORDER BY total_records DESC;