
-- Phase 6: Load to MySQL
-- Script 05: Initial SQL data quality checks

USE automated_data_quality_etl;

-- 1. Check missing values in key columns
SELECT
    SUM(CASE WHEN invoice_no IS NULL OR invoice_no = '' THEN 1 ELSE 0 END) AS missing_invoice_no,
    SUM(CASE WHEN stock_code IS NULL OR stock_code = '' THEN 1 ELSE 0 END) AS missing_stock_code,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS missing_quantity,
    SUM(CASE WHEN invoice_date IS NULL THEN 1 ELSE 0 END) AS missing_invoice_date,
    SUM(CASE WHEN unit_price IS NULL THEN 1 ELSE 0 END) AS missing_unit_price,
    SUM(CASE WHEN country IS NULL OR country = '' THEN 1 ELSE 0 END) AS missing_country
FROM online_retail_feature_engineered;

-- 2. Check negative or zero quantities
SELECT COUNT(*) AS invalid_quantity_records
FROM online_retail_feature_engineered
WHERE quantity <= 0;

-- 3. Check negative or zero unit prices
SELECT COUNT(*) AS invalid_unit_price_records
FROM online_retail_feature_engineered
WHERE unit_price <= 0;

-- 4. Check total amount mismatch
SELECT COUNT(*) AS total_amount_mismatch_records
FROM online_retail_feature_engineered
WHERE ROUND(quantity * unit_price, 2) <> ROUND(total_amount, 2);

-- 5. A source row is unique within this full snapshot.
SELECT source_row_number, COUNT(*) AS duplicate_count
FROM online_retail_feature_engineered
GROUP BY source_row_number HAVING COUNT(*) > 1;

-- 6. Feature distributions
SELECT revenue_category, COUNT(*) AS record_count
FROM online_retail_feature_engineered GROUP BY revenue_category;
SELECT quantity_category, COUNT(*) AS record_count
FROM online_retail_feature_engineered GROUP BY quantity_category;

-- 7. Rounded zero amounts are intentional for sub-penny unit prices.
SELECT COUNT(*) AS zero_rounded_amount_rows
FROM online_retail_feature_engineered WHERE total_amount = 0;
