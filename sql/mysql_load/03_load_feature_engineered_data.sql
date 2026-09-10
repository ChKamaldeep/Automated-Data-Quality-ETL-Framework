-- Loading is owned by retail_etl.database.publish_snapshot.
-- This deliberately contains no positional LOAD DATA or global server changes.
-- After setting MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD,
-- and MYSQL_DATABASE in your environment, run from your terminal:
-- python -m retail_etl --as-of 2011-12-09 --load-mysql
-- It validates a new staging table, atomically publishes it, and retains
-- the previous table as retail_backup_<run token>. Repeated runs replace
-- the snapshot without appending duplicate rows. See docs/database.md.
SELECT 'Use python -m retail_etl --load-mysql from the terminal' AS loading_instruction;
