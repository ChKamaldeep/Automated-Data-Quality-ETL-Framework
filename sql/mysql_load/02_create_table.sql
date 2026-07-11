-- Phase 6: Load to MySQL
-- Script 02: Create table for feature-engineered Online Retail data

USE automated_data_quality_etl;

DROP TABLE IF EXISTS online_retail_feature_engineered;

CREATE TABLE online_retail_feature_engineered (
    invoice_no VARCHAR(50),
    stock_code VARCHAR(50),
    description TEXT,
    quantity INT,
    invoice_date DATETIME,
    unit_price DECIMAL(10,2),
    customer_id VARCHAR(50),
    country VARCHAR(100),

    total_amount DECIMAL(12,2),
    invoice_year INT,
    invoice_month INT,
    invoice_day INT,
    invoice_hour INT,
    day_of_week VARCHAR(20),
    is_weekend VARCHAR(10),

    revenue_category VARCHAR(50),
    quantity_category VARCHAR(50),
    unit_price_category VARCHAR(50),
    customer_type VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);