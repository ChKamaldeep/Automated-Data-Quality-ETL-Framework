-- Population: positive sales with identified customers, excluding cancellations.
-- Includes positive-price lines whose rounded amount is zero. Currency: GBP.
-- ============================================================
-- Phase 7: SQL Analytics & Data Quality
-- File: 01_business_kpis_eda.sql
-- Project: Automated Data Quality & ETL Framework
-- Table: online_retail_feature_engineered
-- Purpose:
--   Business KPI analysis and exploratory SQL checks
-- ============================================================

USE automated_data_quality_etl;

-- Preview table
SELECT *
FROM online_retail_feature_engineered
LIMIT 10;

-- Total records
SELECT 
    COUNT(*) AS total_rows
FROM online_retail_feature_engineered;

-- Business KPI summary
SELECT
    COUNT(DISTINCT invoice_no) AS total_invoices,
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT stock_code) AS total_products,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_line_value,
    ROUND(AVG(quantity), 2) AS avg_quantity,
    ROUND(AVG(unit_price), 2) AS avg_unit_price
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0;

-- Revenue by country
SELECT
    country,
    ROUND(SUM(total_amount), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS invoices,
    COUNT(DISTINCT customer_id) AS customers
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY country
ORDER BY revenue DESC;

-- Top 10 countries by revenue
SELECT
    country,
    ROUND(SUM(total_amount), 2) AS revenue
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY country
ORDER BY revenue DESC
LIMIT 10;

-- Invoice-level revenue
SELECT
    invoice_no,
    customer_id,
    invoice_date,
    ROUND(SUM(total_amount), 2) AS invoice_revenue
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY invoice_no, customer_id, invoice_date
ORDER BY invoice_revenue DESC
LIMIT 20;

-- Cancelled transaction check
SELECT
    COUNT(*) AS cancelled_rows,
    ROUND(SUM(total_amount), 2) AS cancelled_amount
FROM online_retail_feature_engineered
WHERE quantity < 0 OR invoice_no LIKE 'C%';