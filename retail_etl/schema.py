"""The single ordered contract used by Python exports and MySQL inserts."""

SCHEMA_VERSION = "2"
SOURCE_MAPPING = {
    "InvoiceNo": "invoice_no", "StockCode": "stock_code",
    "Description": "description", "Quantity": "quantity",
    "InvoiceDate": "invoice_date", "UnitPrice": "unit_price",
    "CustomerID": "customer_id", "Country": "country",
}
SOURCE_COLUMNS = tuple(SOURCE_MAPPING.values())

# Six decimal places preserve source unit prices (including 0.001 GBP).
# Currency line totals use decimal ROUND_HALF_UP to two places.
COLUMN_TYPES = {
    "invoice_no": "VARCHAR(50) NOT NULL",
    "stock_code": "VARCHAR(50) NOT NULL",
    "description": "TEXT NOT NULL",
    "quantity": "INT NOT NULL",
    "invoice_date": "DATETIME NOT NULL",
    "unit_price": "DECIMAL(18,6) NOT NULL",
    "customer_id": "VARCHAR(50) NOT NULL",
    "country": "VARCHAR(100) NOT NULL",
    "total_amount": "DECIMAL(18,2) NOT NULL",
    "invoice_year": "SMALLINT NOT NULL",
    "invoice_month": "TINYINT NOT NULL",
    "invoice_month_name": "VARCHAR(9) NOT NULL",
    "invoice_day": "TINYINT NOT NULL",
    "invoice_day_name": "VARCHAR(9) NOT NULL",
    "invoice_hour": "TINYINT NOT NULL",
    "invoice_quarter": "TINYINT NOT NULL",
    "year_month": "CHAR(7) NOT NULL",
    "quantity_category": "VARCHAR(6) NOT NULL",
    "revenue_category": "VARCHAR(13) NOT NULL",
    "source_row_number": "BIGINT NOT NULL",
}
OUTPUT_COLUMNS = tuple(COLUMN_TYPES)
TABLE_NAME = "online_retail_feature_engineered"


def create_table_sql(table_name=TABLE_NAME, if_not_exists=False):
    """Generate DDL; never interpolate user-controlled SQL identifiers."""
    import re
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", table_name):
        raise ValueError("Invalid table name")
    fields = [f"    `{name}` {kind}" for name, kind in COLUMN_TYPES.items()]
    fields += [
        "    PRIMARY KEY (`source_row_number`)",
        "    INDEX idx_invoice_date (`invoice_date`)",
        "    INDEX idx_customer_id (`customer_id`)",
        "    INDEX idx_stock_code (`stock_code`)",
        "    INDEX idx_invoice_no (`invoice_no`)",
        "    CHECK (quantity > 0)",
        "    CHECK (unit_price > 0)",
        "    CHECK (total_amount >= 0)",
    ]
    exists = "IF NOT EXISTS " if if_not_exists else ""
    return (f"CREATE TABLE {exists}`{table_name}` (\n" + ",\n".join(fields)
            + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin")
