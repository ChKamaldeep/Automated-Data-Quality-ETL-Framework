-- ============================================================
-- File: 04_time_series_analysis.sql
-- Purpose:
--   Revenue and sales trends over time
-- ============================================================

USE automated_data_quality_etl;

-- Daily revenue trend
SELECT
    DATE(invoice_date) AS invoice_day,
    ROUND(SUM(total_amount), 2) AS daily_revenue,
    COUNT(DISTINCT invoice_no) AS daily_orders
FROM online_retail_feature_engineered
WHERE total_amount > 0
GROUP BY DATE(invoice_date)
ORDER BY invoice_day;

-- Monthly revenue trend
SELECT
    invoice_year,
    invoice_month,
    ROUND(SUM(total_amount), 2) AS monthly_revenue,
    COUNT(DISTINCT invoice_no) AS monthly_orders,
    COUNT(DISTINCT customer_id) AS monthly_customers
FROM online_retail_feature_engineered
WHERE total_amount > 0
GROUP BY invoice_year, invoice_month
ORDER BY invoice_year, invoice_month;

-- Revenue by day of week
SELECT
    DAYNAME(invoice_date) AS invoice_day_name,
    ROUND(SUM(total_amount), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS invoices
FROM online_retail_feature_engineered
WHERE total_amount > 0
GROUP BY DAYNAME(invoice_date)
ORDER BY revenue DESC;

-- Revenue by hour
SELECT
    invoice_hour,
    ROUND(SUM(total_amount), 2) AS hourly_revenue,
    COUNT(DISTINCT invoice_no) AS invoices
FROM online_retail_feature_engineered
WHERE total_amount > 0
GROUP BY invoice_hour
ORDER BY invoice_hour;

-- Quarterly performance
SELECT
    YEAR(invoice_date) AS invoice_year,
    QUARTER(invoice_date) AS invoice_quarter,
    ROUND(SUM(total_amount), 2) AS quarterly_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders
FROM online_retail_feature_engineered
WHERE total_amount > 0
GROUP BY
    YEAR(invoice_date),
    QUARTER(invoice_date)
ORDER BY
    YEAR(invoice_date),
    QUARTER(invoice_date);