-- Population: positive sales with identified customers, excluding cancellations.
-- Includes positive-price lines whose rounded amount is zero. Currency: GBP.
-- ============================================================
-- File: 02_aggregate_groupby_having.sql
-- Purpose:
--   Aggregate analysis using GROUP BY and HAVING
-- ============================================================

USE automated_data_quality_etl;

-- Monthly revenue
SELECT
    invoice_year,
    invoice_month,
    ROUND(SUM(total_amount), 2) AS monthly_revenue,
    COUNT(DISTINCT invoice_no) AS total_invoices
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY invoice_year, invoice_month
ORDER BY invoice_year, invoice_month;

-- Product-level sales
SELECT
    stock_code,
    description,
    SUM(quantity) AS total_quantity_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY stock_code, description
ORDER BY total_revenue DESC
LIMIT 25;

-- Customers with revenue above 5000
SELECT
    customer_id,
    ROUND(SUM(total_amount), 2) AS customer_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders
FROM online_retail_feature_engineered
WHERE customer_id IS NOT NULL
  AND unit_price > 0
GROUP BY customer_id
HAVING SUM(total_amount) > 5000
ORDER BY customer_revenue DESC;

-- Products sold more than 1000 units
SELECT
    stock_code,
    description,
    SUM(quantity) AS total_quantity
FROM online_retail_feature_engineered
WHERE quantity > 0
GROUP BY stock_code, description
HAVING SUM(quantity) > 1000
ORDER BY total_quantity DESC;

-- Countries with more than 100 invoices
SELECT
    country,
    COUNT(DISTINCT invoice_no) AS invoice_count,
    ROUND(SUM(total_amount), 2) AS revenue
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY country
HAVING COUNT(DISTINCT invoice_no) > 100
ORDER BY revenue DESC;