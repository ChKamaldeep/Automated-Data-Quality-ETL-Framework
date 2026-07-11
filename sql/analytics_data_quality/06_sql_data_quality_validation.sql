 -- ============================================================
-- File: 06_sql_data_quality_validation.sql
-- Purpose:
--   SQL-based data quality and validation checks
-- ============================================================

USE automated_data_quality_etl;

-- Null value checks
SELECT
    SUM(CASE WHEN invoice_no IS NULL THEN 1 ELSE 0 END) AS null_invoice_no,
    SUM(CASE WHEN stock_code IS NULL THEN 1 ELSE 0 END) AS null_stock_code,
    SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END) AS null_description,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS null_quantity,
    SUM(CASE WHEN invoice_date IS NULL THEN 1 ELSE 0 END) AS null_invoice_date,
    SUM(CASE WHEN unit_price IS NULL THEN 1 ELSE 0 END) AS null_unit_price,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN country IS NULL THEN 1 ELSE 0 END) AS null_country
FROM online_retail_feature_engineered;

-- Duplicate transaction-line check
SELECT
    invoice_no,
    stock_code,
    customer_id,
    invoice_date,
    quantity,
    unit_price,
    COUNT(*) AS duplicate_count
FROM online_retail_feature_engineered
GROUP BY
    invoice_no,
    stock_code,
    customer_id,
    invoice_date,
    quantity,
    unit_price
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Negative quantity check
SELECT *
FROM online_retail_feature_engineered
WHERE quantity < 0;

-- Zero or negative unit price check
SELECT *
FROM online_retail_feature_engineered
WHERE unit_price <= 0;

-- Invalid revenue calculation check
SELECT
    invoice_no,
    stock_code,
    quantity,
    unit_price,
    total_amount,
    ROUND(quantity * unit_price, 2) AS recalculated_amount
FROM online_retail_feature_engineered
WHERE ROUND(total_amount, 2) <> ROUND(quantity * unit_price, 2);

-- Future invoice date check
SELECT *
FROM online_retail_feature_engineered
WHERE invoice_date > CURRENT_DATE();

-- Blank text field checks
SELECT *
FROM online_retail_feature_engineered
WHERE TRIM(invoice_no) = ''
   OR TRIM(stock_code) = ''
   OR TRIM(country) = '';

-- Customer IDs with abnormal revenue
SELECT
    customer_id,
    ROUND(SUM(total_amount), 2) AS revenue
FROM online_retail_feature_engineered
WHERE customer_id IS NOT NULL
GROUP BY customer_id
HAVING revenue < 0
ORDER BY revenue;