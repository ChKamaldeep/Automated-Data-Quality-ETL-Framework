-- Population: positive sales with identified customers, excluding cancellations.
-- Includes positive-price lines whose rounded amount is zero. Currency: GBP.
-- ============================================================
-- File: 03_customer_product_revenue_analysis.sql
-- Purpose:
--   Customer, product, and revenue analytics
-- ============================================================

USE automated_data_quality_etl;

-- Top customers by revenue
SELECT
    customer_id,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders,
    ROUND(AVG(total_amount), 2) AS avg_line_value
FROM online_retail_feature_engineered
WHERE customer_id IS NOT NULL
  AND unit_price > 0
GROUP BY customer_id
ORDER BY total_revenue DESC
LIMIT 20;

-- Customer purchase frequency
SELECT
    customer_id,
    COUNT(DISTINCT invoice_no) AS purchase_frequency,
    ROUND(SUM(total_amount), 2) AS revenue
FROM online_retail_feature_engineered
WHERE customer_id IS NOT NULL
  AND unit_price > 0
GROUP BY customer_id
ORDER BY purchase_frequency DESC
LIMIT 20;

-- Top products by quantity sold
SELECT
    stock_code,
    description,
    SUM(quantity) AS quantity_sold
FROM online_retail_feature_engineered
WHERE quantity > 0
GROUP BY stock_code, description
ORDER BY quantity_sold DESC
LIMIT 20;

-- Top products by revenue
SELECT
    stock_code,
    description,
    ROUND(SUM(total_amount), 2) AS product_revenue
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY stock_code, description
ORDER BY product_revenue DESC
LIMIT 20;

-- Average order value by country
SELECT
    country,
    ROUND(SUM(total_amount) / COUNT(DISTINCT invoice_no), 2) AS avg_order_value
FROM online_retail_feature_engineered
WHERE quantity > 0 AND unit_price > 0
GROUP BY country
ORDER BY avg_order_value DESC;

-- Repeat customer analysis
SELECT
    customer_id,
    COUNT(DISTINCT invoice_no) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    CASE
        WHEN COUNT(DISTINCT invoice_no) = 1 THEN 'One-Time Customer'
        WHEN COUNT(DISTINCT invoice_no) BETWEEN 2 AND 5 THEN 'Repeat Customer'
        ELSE 'Frequent Repeat Customer'
    END AS customer_segment
FROM online_retail_feature_engineered
WHERE customer_id IS NOT NULL
  AND unit_price > 0
GROUP BY customer_id
ORDER BY total_revenue DESC;