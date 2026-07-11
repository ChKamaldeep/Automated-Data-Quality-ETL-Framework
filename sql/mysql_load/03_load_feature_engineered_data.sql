-- Phase 6: Load to MySQL
-- Script 03: Load feature-engineered CSV into MySQL

USE automated_data_quality_etl;
SET GLOBAL local_infile = 1;


LOAD DATA LOCAL INFILE 'C:/Users/chatu/OneDrive/Desktop/Automated-Data-Quality-ETL-Framework/outputs/feature_engineered_online_retail.csv'
INTO TABLE online_retail_feature_engineered
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    invoice_no,
    stock_code,
    description,
    quantity,
    invoice_date,
    unit_price,
    customer_id,
    country,
    total_amount,
    invoice_year,
    invoice_month,
    invoice_day,
    invoice_hour,
    day_of_week,
    is_weekend,
    revenue_category,
    quantity_category,
    unit_price_category,
    customer_type
);




