-- Generated from retail_etl.schema. Never drops existing data.
-- Existing v1 tables are migrated by the staging publisher, not CREATE IF NOT EXISTS.
USE automated_data_quality_etl;

CREATE TABLE IF NOT EXISTS `online_retail_feature_engineered` (
    `invoice_no` VARCHAR(50) NOT NULL,
    `stock_code` VARCHAR(50) NOT NULL,
    `description` TEXT NOT NULL,
    `quantity` INT NOT NULL,
    `invoice_date` DATETIME NOT NULL,
    `unit_price` DECIMAL(18,6) NOT NULL,
    `customer_id` VARCHAR(50) NOT NULL,
    `country` VARCHAR(100) NOT NULL,
    `total_amount` DECIMAL(18,2) NOT NULL,
    `invoice_year` SMALLINT NOT NULL,
    `invoice_month` TINYINT NOT NULL,
    `invoice_month_name` VARCHAR(9) NOT NULL,
    `invoice_day` TINYINT NOT NULL,
    `invoice_day_name` VARCHAR(9) NOT NULL,
    `invoice_hour` TINYINT NOT NULL,
    `invoice_quarter` TINYINT NOT NULL,
    `year_month` CHAR(7) NOT NULL,
    `quantity_category` VARCHAR(6) NOT NULL,
    `revenue_category` VARCHAR(13) NOT NULL,
    `source_row_number` BIGINT NOT NULL,
    PRIMARY KEY (`source_row_number`),
    INDEX idx_invoice_date (`invoice_date`),
    INDEX idx_customer_id (`customer_id`),
    INDEX idx_stock_code (`stock_code`),
    INDEX idx_invoice_no (`invoice_no`),
    CHECK (quantity > 0),
    CHECK (unit_price > 0),
    CHECK (total_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
