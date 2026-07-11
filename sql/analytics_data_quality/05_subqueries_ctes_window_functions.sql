-- ============================================================
-- File: 05_subqueries_ctes_window_functions.sql
-- Purpose:
--   Advanced SQL using subqueries, CTEs, and window functions
-- ============================================================

USE automated_data_quality_etl;

-- Subquery: customers above average revenue
SELECT
    customer_id,
    ROUND(SUM(total_amount), 2) AS customer_revenue
FROM online_retail_feature_engineered
WHERE customer_id IS NOT NULL
  AND total_amount > 0
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(customer_total)
    FROM (
        SELECT SUM(total_amount) AS customer_total
        FROM online_retail_feature_engineered
        WHERE customer_id IS NOT NULL
          AND total_amount > 0
        GROUP BY customer_id
    ) AS customer_totals
)
ORDER BY customer_revenue DESC;

-- CTE: customer revenue ranking
WITH customer_revenue AS (
    SELECT
        customer_id,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM online_retail_feature_engineered
    WHERE customer_id IS NOT NULL
      AND total_amount > 0
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM customer_revenue
ORDER BY revenue_rank
LIMIT 25;

-- ROW_NUMBER: top product per country
WITH country_product_revenue AS (
    SELECT
        country,
        stock_code,
        description,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM online_retail_feature_engineered
    WHERE total_amount > 0
    GROUP BY country, stock_code, description
),
ranked_products AS (
    SELECT
        country,
        stock_code,
        description,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY country
            ORDER BY revenue DESC
        ) AS row_num
    FROM country_product_revenue
)
SELECT *
FROM ranked_products
WHERE row_num = 1
ORDER BY revenue DESC;

-- RANK and DENSE_RANK: product revenue ranking
WITH product_revenue AS (
    SELECT
        stock_code,
        description,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM online_retail_feature_engineered
    WHERE total_amount > 0
    GROUP BY stock_code, description
)
SELECT
    stock_code,
    description,
    revenue,
    RANK() OVER (ORDER BY revenue DESC) AS product_rank,
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS dense_product_rank
FROM product_revenue
ORDER BY revenue DESC
LIMIT 25;

-- LAG: month-over-month revenue change
WITH monthly_revenue AS (
    SELECT
        invoice_year,
        invoice_month,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM online_retail_feature_engineered
    WHERE total_amount > 0
    GROUP BY invoice_year, invoice_month
)
SELECT
    invoice_year,
    invoice_month,
    revenue,
    LAG(revenue) OVER (
        ORDER BY invoice_year, invoice_month
    ) AS previous_month_revenue,
    ROUND(
        revenue - LAG(revenue) OVER (ORDER BY invoice_year, invoice_month),
        2
    ) AS revenue_change
FROM monthly_revenue
ORDER BY invoice_year, invoice_month;

-- LEAD: next month revenue comparison
WITH monthly_revenue AS (
    SELECT
        invoice_year,
        invoice_month,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM online_retail_feature_engineered
    WHERE total_amount > 0
    GROUP BY invoice_year, invoice_month
)
SELECT
    invoice_year,
    invoice_month,
    revenue,
    LEAD(revenue) OVER (
        ORDER BY invoice_year, invoice_month
    ) AS next_month_revenue
FROM monthly_revenue
ORDER BY invoice_year, invoice_month;