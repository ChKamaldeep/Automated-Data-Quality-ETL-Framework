-- Population: positive sales with identified customers, excluding cancellations.
-- Includes positive-price lines whose rounded amount is zero. Currency: GBP.
-- ============================================================
-- File: 07_views.sql
-- Purpose:
--   Reusable SQL views for analytics and dashboarding
-- ============================================================

USE automated_data_quality_etl;

-- View 1: clean positive sales only
CREATE OR REPLACE VIEW vw_positive_sales AS
SELECT *
FROM online_retail_feature_engineered
WHERE quantity > 0
  AND unit_price > 0;

-- View 2: monthly revenue summary
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    invoice_year,
    invoice_month,
    ROUND(SUM(total_amount), 2) AS monthly_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers
FROM vw_positive_sales
GROUP BY invoice_year, invoice_month;

-- View 3: customer revenue summary
CREATE OR REPLACE VIEW vw_customer_revenue AS
SELECT
    customer_id,
    COUNT(DISTINCT invoice_no) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_line_value,
    MIN(invoice_date) AS first_purchase_date,
    MAX(invoice_date) AS last_purchase_date
FROM vw_positive_sales
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- View 4: product performance summary
CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    stock_code,
    description,
    SUM(quantity) AS total_quantity_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    COUNT(DISTINCT invoice_no) AS order_count
FROM vw_positive_sales
GROUP BY stock_code, description;

-- View 5: country revenue summary
CREATE OR REPLACE VIEW vw_country_revenue AS
SELECT
    country,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM vw_positive_sales
GROUP BY country;
