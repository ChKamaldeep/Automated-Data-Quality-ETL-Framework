-- Population: positive sales with identified customers, excluding cancellations.
-- Includes positive-price lines whose rounded amount is zero. Currency: GBP.
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

-- Source-row identity is the key; repeated invoice/product combinations can be valid.
SELECT source_row_number, COUNT(*) AS duplicate_count
FROM online_retail_feature_engineered
GROUP BY source_row_number HAVING COUNT(*) > 1;

-- Negative quantity check
SELECT *
FROM online_retail_feature_engineered
WHERE quantity <= 0;

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
WHERE invoice_date >= CURRENT_DATE() + INTERVAL 1 DAY;

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