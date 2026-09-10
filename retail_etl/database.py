"""Publish a validated full snapshot to MySQL 8.0.16+.

Rows are loaded into a new staging table and verified before one atomic RENAME.
The old table is retained as a backup. No live table is dropped or truncated.
"""

from decimal import Decimal
import os
import re
import uuid

from .schema import TABLE_NAME, OUTPUT_COLUMNS, create_table_sql
from .transform import validate_output


def connect_from_environment():
    import mysql.connector
    required = [k for k in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE") if k not in os.environ]
    if required:
        raise ValueError("Missing database settings: " + ", ".join(required))
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"], autocommit=False,
        charset="utf8mb4", connection_timeout=15,
        allow_local_infile=False,
    )


def publish_snapshot(df, *, connection=None, batch_size=2000):
    """Safe on repeated input: replace the snapshot, never append to live data.

    The advisory lock serializes publishers using this function. Other writers
    must not modify this analytical table. A fresh database requires the database
    itself to exist; no global server settings or root account are needed.
    """
    expected = validate_output(df)
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    owns_connection = connection is None
    conn = connection if connection is not None else connect_from_environment()
    cursor = None
    locked = staged = published = False
    token = uuid.uuid4().hex[:16]
    stage, backup = f"retail_stage_{token}", f"retail_backup_{token}"
    lock_name = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION(), DATABASE()")
        version, database = cursor.fetchone()
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
        if "MariaDB" in version or not match or tuple(map(int, match.groups())) < (8, 0, 16):
            raise ValueError("MySQL Server 8.0.16+ is required for enforced CHECK constraints")
        # Keep the lock name inside MySQL's 64-character limit.
        import hashlib
        lock_name = "retail_etl:" + hashlib.sha256(database.encode()).hexdigest()[:40]
        cursor.execute("SELECT GET_LOCK(%s, 10)", (lock_name,))
        if cursor.fetchone()[0] != 1:
            raise RuntimeError("Another ETL publisher holds the database lock")
        locked = True
        cursor.execute("SET SESSION sql_mode = 'STRICT_ALL_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
        cursor.execute(create_table_sql(stage))
        staged = True
        columns = ", ".join(f"`{c}`" for c in OUTPUT_COLUMNS)
        placeholders = ", ".join(["%s"] * len(OUTPUT_COLUMNS))
        insert = f"INSERT INTO `{stage}` ({columns}) VALUES ({placeholders})"
        for offset in range(0, len(df), batch_size):
            batch = df.iloc[offset:offset + batch_size]
            rows = [tuple(v.to_pydatetime() if hasattr(v, "to_pydatetime")
                          else v.item() if hasattr(v, "item") else v for v in row)
                    for row in batch.itertuples(index=False, name=None)]
            cursor.executemany(insert, rows)
            cursor.execute("SHOW WARNINGS")
            if cursor.fetchall():
                raise ValueError("MySQL reported a load warning; live snapshot was not changed")
        cursor.execute(f"SELECT COUNT(*), COALESCE(SUM(total_amount), 0) FROM `{stage}`")
        count, amount = cursor.fetchone()
        if count != expected["rows"] or Decimal(str(amount)) != Decimal(expected["total_amount"]):
            raise ValueError("Database row count or amount reconciliation failed")
        cursor.execute(f"""SELECT COUNT(*) FROM `{stage}`
            WHERE total_amount <> ROUND(quantity * unit_price, 2)
               OR invoice_year <> YEAR(invoice_date)
               OR invoice_month <> MONTH(invoice_date)
               OR invoice_day <> DAY(invoice_date)
               OR invoice_hour <> HOUR(invoice_date)
               OR invoice_quarter <> QUARTER(invoice_date)
               OR `year_month` <> DATE_FORMAT(invoice_date, '%Y-%m')""")
        if cursor.fetchone()[0]:
            raise ValueError("Database derived-value validation failed")
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables "
                       "WHERE table_schema=DATABASE() AND table_name=%s", (TABLE_NAME,))
        exists = cursor.fetchone()[0] > 0
        rename = (f"RENAME TABLE `{TABLE_NAME}` TO `{backup}`, `{stage}` TO `{TABLE_NAME}`"
                  if exists else f"RENAME TABLE `{stage}` TO `{TABLE_NAME}`")
        cursor.execute(rename)
        published = True
        # RENAME is the commit point. No post-publication query is needed for success.
        return {"status": "published", "table": TABLE_NAME, "rows": count,
                "total_amount": str(amount), "backup_table": backup if exists else None}
    except Exception:
        conn.rollback()
        if staged and not published and cursor is not None:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS `{stage}`")
            except Exception:
                # Preserve the original failure. A leftover staging table is never live.
                pass
        raise
    finally:
        if cursor is not None:
            if locked:
                try:
                    cursor.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
                    cursor.fetchone()
                except Exception:
                    pass
            cursor.close()
        if owns_connection:
            conn.close()
