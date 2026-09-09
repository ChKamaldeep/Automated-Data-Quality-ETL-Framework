# Automated Data Quality & ETL Framework

A Python and MySQL portfolio project by **Kamaldeep**. It turns the UCI Online Retail source into a validated sales dataset with traceable exclusions, reproducible exports, and an optional verified database load.

## Verified result

A full source run on 9 September 2026, using the inclusive cutoff `2011-12-09`, produced:

| Measure | Result |
|---|---:|
| Source rows | 541,909 |
| Accepted sales lines | 392,692 |
| Excluded rows, retained with reasons | 149,217 |
| Output columns | 20 |
| Sum of rounded sales line amounts (GBP) | 8,887,208.89 |
| Positive-price lines rounded to zero | 4 |

This is **positive sales for identified customers, excluding cancellations**. It is not net company revenue: anonymous purchases and returns are outside this analytical population. Source exclusions can overlap; use the unique rejected-row count for reconciliation.

[Verification details](docs/verification.md) · [Data contract](docs/data_contract.md) · [Database setup and migration](docs/database.md)

## Quick start

Use Python 3.11–3.13. MySQL is optional for the CSV workflow.

```bash
git clone https://github.com/ChKamaldeep/Automated-Data-Quality-ETL-Framework.git
cd Automated-Data-Quality-ETL-Framework
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
python -m retail_etl --as-of 2011-12-09
```

The bundled Excel source is read without modification. For another input:

```bash
python -m retail_etl --input path/to/source.csv --output-dir outputs --as-of 2026-09-09
```

CSV inputs must use the eight documented source columns and ISO timestamps. Change the inclusive cutoff to match the source reporting period. The default, when omitted, is the current UTC calendar date. Invoice timestamps themselves remain timezone-naive source-local timestamps.

## What a run produces

Each execution writes to `outputs/runs/<run_id>/`:

| File | Purpose |
|---|---|
| `cleaned_online_retail_data.csv` | Accepted source fields plus source row identity |
| `feature_engineered_online_retail.csv` | Canonical 20-column analytical dataset |
| `rejected_rows.csv` | Excluded original records with source row numbers and reasons |
| `validation.json` | Counts by rule, accepted rows, and rejected rows |
| `manifest.json` | Input/output hashes, schema version, run status, timings, and database outcome |
| `pipeline.log` | Stage progress and exception tracebacks; rotates if large |

`outputs/latest.json` points to the latest successful run. Failed runs retain diagnostics and do not advance that pointer. Resolve the `data` path inside this JSON relative to `outputs/` to locate the final CSV. A failed run can contain incomplete files; only consume successful runs.

Generated data and screenshots from the earlier implementation are no longer tracked as current results. The original versions remain in Git history. This avoids stale CSVs disagreeing with current code; the new run manifest is the audit record.

## MySQL loading

Install **MySQL Server 8.0.16 or later**. MySQL Workbench is an optional SQL client, not the database server.

1. Create the database with `sql/mysql_load/01_create_database.sql`.
2. Configure the `MYSQL_*` environment variables described in [database.md](docs/database.md).
3. Run:

```bash
python -m retail_etl --as-of 2011-12-09 --load-mysql
```

The publisher loads a staging table using parameterized inserts with explicit column names. It rejects database warnings, reconciles row counts and amounts, checks derived values, and publishes through an atomic table rename. It preserves the prior table as `retail_backup_<token>`. Repeated input replaces the snapshot instead of appending duplicate rows.

After publishing, run the SQL files in `sql/analytics_data_quality/` in numerical order. They include KPIs, grouped analyses, date trends, window functions, checks, views, and repeatable stored-procedure setup. SQL scripts use the default database name; change their `USE` statements if using another database.

## Learning notebooks

Install the notebook/test tools:

```bash
python -m pip install -e ".[dev]"
python -m jupyterlab
```

| Notebook | Focus |
|---|---|
| `01_Data_Profiling.ipynb` | Source shape, types, nulls, duplicates, and quality flags |
| `02_Data_Validation.ipynb` | Shared validation rules and row reconciliation |
| `03_Data_Cleaning_Transformation.ipynb` | Normalization, exclusions, and currency precision |
| `04_Feature_Engineering.ipynb` | Canonical features, invoice totals, and customer frequency |
| `05_ETL_Pipeline_Automation.ipynb` | Complete CSV pipeline with manifest and logging |

Notebooks 1–4 explore the shared functions without overwriting exports. Notebook 5 calls the same runner as the CLI. Each notebook can run independently. Optional `RETAIL_ETL_INPUT` and `RETAIL_ETL_OUTPUT` environment variables support sample data or another output directory.

## Tests and dependencies

```bash
python -m pytest -q
```

Tests cover invalid records, precision, source reconciliation, output contracts, repeated input, failure handling, and execution of every notebook code cell. MySQL integration tests require an explicit opt-in and create their own temporary databases; see [database.md](docs/database.md).

GitHub Actions defines Python 3.11–3.13 jobs and a MySQL 8.0 service job. See the actual workflow run for execution status. `pyproject.toml` defines supported dependency ranges; `requirements-lock.txt` records the core versions used for the full-data verification on Python 3.12.

## Layout

- `retail_etl/`: shared schema, transformations, file runner, database publisher, and CLI.
- `notebooks/`: learning walkthroughs that import the package.
- `sql/`: database setup and business analytics.
- `tests/`: unit, notebook, and database integration checks.
- `docs/`: data rules, migration instructions, and verification evidence.
- `data/raw/`: original UCI workbook, preserved unchanged.

## Scope and next steps

This implementation is a local batch pipeline that reads the dataset into memory. It supports full snapshot replacement, not incremental ingestion or change-data capture. Database views and procedures are installed separately. Run directories and database backups require deliberate retention management. CSV publication and database publication cannot share one transaction; the manifest records the database outcome separately.

A useful next extension is an incremental-load design with stable upstream event IDs. A scheduler, Docker setup, or dashboard can be added after choosing an operating environment; none is claimed as implemented here.

## Dataset attribution

Chen, D. (2015). **Online Retail** [Dataset]. UCI Machine Learning Repository. [DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33). The dataset covers 1 December 2010 through 9 December 2011 and uses sterling unit prices. It is distributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Derived exports apply the transformations documented in this repository. [Source dataset](https://archive.ics.uci.edu/dataset/352/online+retail).

The earlier MIT badge has been removed because this repository does not contain a standalone code license.
