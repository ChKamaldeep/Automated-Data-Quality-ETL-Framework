"""Integration tests create and remove their own uniquely named test database."""
import os
from pathlib import Path
import uuid

import pytest

from retail_etl import database
from retail_etl.schema import OUTPUT_COLUMNS, TABLE_NAME
from retail_etl.transform import prepare_data, feature_engineering

pytestmark = [pytest.mark.mysql, pytest.mark.skipif(
    os.getenv("RETAIL_ETL_MYSQL_TESTS") != "1", reason="Set RETAIL_ETL_MYSQL_TESTS=1 for isolated MySQL tests")]


@pytest.fixture
def connection():
    import mysql.connector
    name = "retail_etl_test_" + uuid.uuid4().hex[:12]
    settings = dict(host=os.getenv("MYSQL_HOST", "127.0.0.1"),
                    port=int(os.getenv("MYSQL_PORT", "3306")),
                    user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"])
    admin = mysql.connector.connect(**settings, autocommit=True)
    cursor = admin.cursor()
    cursor.execute(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin")
    conn = mysql.connector.connect(**settings, database=name, autocommit=False)
    try:
        yield conn
    finally:
        conn.close()
        cursor.execute(f"DROP DATABASE `{name}`")
        cursor.close()
        admin.close()


def final_data(source):
    return feature_engineering(prepare_data(source, as_of="2011-12-09").cleaned)


def test_publish_twice_preserves_schema_values_and_counts(connection, source):
    source.loc[0, "UnitPrice"] = "0.001"
    data = final_data(source)
    first = database.publish_snapshot(data, connection=connection)
    second = database.publish_snapshot(data, connection=connection, batch_size=1)
    assert first["backup_table"] is None
    assert second["backup_table"].startswith("retail_backup_")
    cursor = connection.cursor()
    cursor.execute(f"SHOW COLUMNS FROM `{TABLE_NAME}`")
    assert tuple(row[0] for row in cursor.fetchall()) == OUTPUT_COLUMNS
    cursor.execute(f"SELECT COUNT(*), SUM(total_amount) FROM `{TABLE_NAME}`")
    count, amount = cursor.fetchone()
    assert count == len(data)
    assert amount == sum(data.total_amount)
    cursor.execute(f"SELECT invoice_month_name, invoice_day, unit_price, total_amount FROM `{TABLE_NAME}` ORDER BY source_row_number")
    row = cursor.fetchone()
    assert row[0:2] == ("December", 1)
    assert str(row[2]) == "0.001000"
    assert str(row[3]) == "0.01"
    cursor.fetchall()
    cursor.close()


def test_migration_retains_old_table_and_failed_load_keeps_live_snapshot(connection, source, monkeypatch):
    cursor = connection.cursor()
    cursor.execute(f"CREATE TABLE `{TABLE_NAME}` (legacy_marker INT)")
    cursor.execute(f"INSERT INTO `{TABLE_NAME}` VALUES (42)")
    connection.commit()
    data = final_data(source)
    result = database.publish_snapshot(data, connection=connection)
    cursor.execute(f"SELECT legacy_marker FROM `{result['backup_table']}`")
    assert cursor.fetchone()[0] == 42
    original = database.create_table_sql
    monkeypatch.setattr(database, "create_table_sql", lambda name: original(name).replace("CHECK (quantity > 0)", "CHECK (quantity > 100)"))
    with pytest.raises(Exception, match="[Cc]heck constraint"):
        database.publish_snapshot(data, connection=connection)
    cursor.execute(f"SELECT COUNT(*), SUM(total_amount) FROM `{TABLE_NAME}`")
    assert cursor.fetchone() == (len(data), sum(data.total_amount))
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name LIKE 'retail_stage_%'")
    assert cursor.fetchone()[0] == 0
    cursor.close()


def statements(script):
    """Handle the mysql client's DELIMITER directives in stored-procedure files."""
    delimiter, pending = ";", ""
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split()[1]
        elif not stripped.startswith("--"):
            pending += line + "\n"
            if pending.rstrip().endswith(delimiter):
                yield pending.rstrip()[:-len(delimiter)]
                pending = ""


def test_all_analytics_and_procedures_execute_twice(connection, source):
    database.publish_snapshot(final_data(source), connection=connection)
    cursor = connection.cursor()
    root = Path(__file__).resolve().parents[1]
    scripts = sorted((root / "sql/analytics_data_quality").glob("*.sql"))
    scripts += [root / "sql/mysql_load/04_verify_load.sql", root / "sql/mysql_load/05_initial_data_quality_checks.sql"]
    for _ in range(2):
        for path in scripts:
            text = path.read_text().replace("USE automated_data_quality_etl;", "")
            for sql in statements(text):
                cursor.execute(sql)
                if cursor.with_rows:
                    cursor.fetchall()
    cursor.execute("CALL sp_revenue_by_date_range('2011-12-01', '2011-12-02')")
    assert len(cursor.fetchall()) == 2
    while cursor.nextset():
        pass
    cursor.execute("CALL sp_top_products_by_revenue(1)")
    assert len(cursor.fetchall()) == 1
    while cursor.nextset():
        pass
    cursor.execute("CALL sp_customer_purchase_summary('17850')")
    assert cursor.fetchone()[1] == 2
    cursor.fetchall()
    while cursor.nextset():
        pass
    cursor.close()
