-- ============================================================
-- File: 08_stored_procedures.sql
-- Purpose:
--   Reusable stored procedures for analytics
-- ============================================================

USE automated_data_quality_etl;


DELIMITER $$

-- Procedure 1: revenue by date range
CREATE PROCEDURE sp_revenue_by_date_range(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT
        DATE(invoice_date) AS invoice_day,
        ROUND(SUM(total_amount), 2) AS revenue,
        COUNT(DISTINCT invoice_no) AS orders
    FROM online_retail_feature_engineered
    WHERE DATE(invoice_date) BETWEEN start_date AND end_date
      AND total_amount > 0
    GROUP BY DATE(invoice_date)
    ORDER BY invoice_day;
END $$

-- Procedure 2: top N products by revenue

DELIMITER $$
CREATE PROCEDURE sp_top_products_by_revenue(
    IN top_n INT
)
BEGIN
    SELECT
        stock_code,
        description,
        ROUND(SUM(total_amount), 2) AS revenue,
        SUM(quantity) AS quantity_sold
    FROM online_retail_feature_engineered
    WHERE total_amount > 0
    GROUP BY stock_code, description
    ORDER BY revenue DESC
    LIMIT top_n;
END $$

-- Procedure 3: customer purchase summary

DELIMITER $$
CREATE PROCEDURE sp_customer_purchase_summary(
    IN input_customer_id DOUBLE
)
BEGIN
    SELECT
        customer_id,
        COUNT(DISTINCT invoice_no) AS total_orders,
        ROUND(SUM(total_amount), 2) AS total_revenue,
        MIN(invoice_date) AS first_purchase_date,
        MAX(invoice_date) AS last_purchase_date
    FROM online_retail_feature_engineered
    WHERE customer_id = input_customer_id
      AND total_amount > 0
    GROUP BY customer_id;
END $$

DELIMITER ;