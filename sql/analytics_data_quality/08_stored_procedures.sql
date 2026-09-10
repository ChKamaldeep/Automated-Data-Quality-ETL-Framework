-- Population: positive sales with identified customers, excluding cancellations.
-- Includes positive-price lines whose rounded amount is zero. Currency: GBP.
-- ============================================================
-- File: 08_stored_procedures.sql
-- Purpose:
--   Reusable stored procedures for analytics
-- ============================================================

USE automated_data_quality_etl;


DROP PROCEDURE IF EXISTS sp_revenue_by_date_range;
DROP PROCEDURE IF EXISTS sp_top_products_by_revenue;
DROP PROCEDURE IF EXISTS sp_customer_purchase_summary;

DELIMITER $$

-- Procedure 1: revenue by date range
CREATE PROCEDURE sp_revenue_by_date_range(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    IF start_date IS NULL OR end_date IS NULL OR start_date > end_date THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Provide a valid inclusive date range';
    END IF;
    SELECT
        DATE(invoice_date) AS invoice_day,
        ROUND(SUM(total_amount), 2) AS revenue,
        COUNT(DISTINCT invoice_no) AS orders
    FROM online_retail_feature_engineered
    WHERE invoice_date >= start_date
      AND invoice_date < end_date + INTERVAL 1 DAY
      AND unit_price > 0
    GROUP BY DATE(invoice_date)
    ORDER BY invoice_day;
END $$

-- Procedure 2: top N products by revenue

DELIMITER $$
CREATE PROCEDURE sp_top_products_by_revenue(
    IN top_n INT
)
BEGIN
    IF top_n IS NULL OR top_n < 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'top_n must be positive';
    END IF;
    SELECT
        stock_code,
        description,
        ROUND(SUM(total_amount), 2) AS revenue,
        SUM(quantity) AS quantity_sold
    FROM online_retail_feature_engineered
    WHERE quantity > 0 AND unit_price > 0
    GROUP BY stock_code, description
    ORDER BY revenue DESC
    LIMIT top_n;
END $$

-- Procedure 3: customer purchase summary

DELIMITER $$
CREATE PROCEDURE sp_customer_purchase_summary(
    IN input_customer_id VARCHAR(50)
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
      AND unit_price > 0
    GROUP BY customer_id;
END $$

DELIMITER ;