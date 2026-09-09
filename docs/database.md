# MySQL setup, migration, and recovery

## Setup

Use MySQL **Server** 8.0.16+ with InnoDB. Workbench is an optional client. The loader does not require `LOCAL INFILE`, changes to global server settings, or a root runtime account.

Create `automated_data_quality_etl` using `sql/mysql_load/01_create_database.sql`. An administrator should provide a dedicated account with SELECT, INSERT, CREATE, ALTER, DROP, and INDEX privileges on this database. DROP is required for the rename operation and staging cleanup; the publisher never drops the previous live snapshot. Installing views and routines separately also needs the corresponding view/routine privileges.

Configure these environment variables in the terminal that will run Python:

| Variable | Meaning | Default |
|---|---|---|
| `MYSQL_HOST` | Database host | `127.0.0.1` |
| `MYSQL_PORT` | Server TCP port | `3306` |
| `MYSQL_USER` | Dedicated database account | Required |
| `MYSQL_PASSWORD` | Account password | Required |
| `MYSQL_DATABASE` | Existing database name | Required |

PowerShell example (the credential dialog collects the password):

```powershell
$etlCredential = Get-Credential -UserName retail_etl -Message "MySQL ETL credentials"
$env:MYSQL_USER = $etlCredential.UserName
$env:MYSQL_PASSWORD = $etlCredential.GetNetworkCredential().Password
$env:MYSQL_DATABASE = "automated_data_quality_etl"
python -m retail_etl --as-of 2011-12-09 --load-mysql
Remove-Item Env:MYSQL_PASSWORD
```

Bash example:

```bash
export MYSQL_USER=retail_etl
export MYSQL_DATABASE=automated_data_quality_etl
read -rs -p 'MySQL password: ' MYSQL_PASSWORD
export MYSQL_PASSWORD
python -m retail_etl --as-of 2011-12-09 --load-mysql
unset MYSQL_PASSWORD
```

The package reads the environment directly; it does not automatically load `.env` files. Do not put credentials in notebooks or commits.

## Publication and repeated runs

1. Validate the canonical DataFrame before connecting.
2. Acquire an advisory lock scoped to this database, serializing this publisher's runs.
3. Create a unique InnoDB staging table with all 20 canonical columns, constraints, and indexes.
4. Insert parameterized batches with explicit column names under strict SQL mode. Abort on database warnings.
5. Reconcile the row count and decimal amount sum and check date/revenue calculations.
6. Commit the staging table, then atomically rename it to `online_retail_feature_engineered`. If an older live table exists, rename it to `retail_backup_<token>` in the same statement.

This is **full snapshot replacement**. Running identical input twice does not duplicate the live rows. `source_row_number` is unique within a source file, not a global incremental event key. Only this publisher should write the analytical table; it is not a general migration mechanism for tables with external writers, foreign-key relationships, or application triggers.

MySQL documents multi-table renames and their atomic behavior in [RENAME TABLE](https://dev.mysql.com/doc/refman/8.0/en/rename-table.html). The old snapshot remains readable until the publish step; the short rename may wait for existing readers' metadata locks.

## Migrating the original project

The old SQL table expected different columns from the CSV. Do not reuse the earlier positional `LOAD DATA` script.

Run the new publisher against the project database. It stages the new schema and retains the existing table as a backup without relying on its old column definitions. The backup table name is recorded in the run manifest. `02_create_table.sql` documents the generated schema and creates it only if absent; it does not migrate an existing table.

After publication, run `sql/analytics_data_quality/01...08` in numerical order, particularly the updated view and procedure definitions. Their setup is repeatable. Stored-procedure replacement briefly removes a routine; install these during a suitable maintenance window if other users call them.

The old fields `day_of_week`, `is_weekend`, `unit_price_category`, and `customer_type` are not present in the canonical export. Use `invoice_day_name`, derive weekends with `DAYOFWEEK(invoice_date) IN (1,7)`, and use the documented shared categories. Customer frequency is computed over distinct invoices in the analytics queries. Update any external Power BI queries that depend on old column names before pointing them at the new schema.

## Failure and retention behavior

Before the rename, an exception rolls back pending inserts and attempts to remove the staging table. The previous live table is preserved. A process kill can leave an unreferenced staging table; inspect it before removing it manually. Backups and prior file runs are retained until you deliberately retire them; no automatic deletion policy is installed.

CSV files and MySQL do not participate in one distributed transaction. A database publish can succeed while a later local manifest/pointer write fails. Check the manifest's `database` outcome and the server table when diagnosing failures. A network interruption at the rename commit point can make the outcome unknown; a `publishing` state must not be assumed to mean the database was unchanged. Re-running a verified source safely replaces the snapshot again.

To restore a retained snapshot, stop other publishers, inspect the backup named in the manifest, and perform an atomic rename in the project database. Replace the example names with verified table names:

```sql
RENAME TABLE online_retail_feature_engineered TO retail_before_restore,
             retail_backup_REPLACE_WITH_TOKEN TO online_retail_feature_engineered;
```

Ensure `retail_before_restore` does not already exist. Restoring a v1 backup also restores its old schema, so matching view/procedure definitions may need to be restored from the earlier Git commit.

## Integration tests

The tests create uniquely named `retail_etl_test_<token>` databases, exercise publication and failures, and remove only those test databases. Use a **test** account allowed to create/drop these disposable databases, with the MYSQL_HOST/PORT/USER/PASSWORD variables set.

```powershell
$env:RETAIL_ETL_MYSQL_TESTS = "1"
python -m pytest -m mysql -q
```

```bash
RETAIL_ETL_MYSQL_TESTS=1 python -m pytest -m mysql -q
```

Tests cover repeated publication, exact column/value mapping, legacy-table backup, failure before publication, and execution of all analytical SQL and routines twice. GitHub Actions provisions a disposable MySQL 8.0 service for these checks; its password is test-only.
