"""File orchestration, run manifests, and failure logging."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from time import perf_counter
import uuid

import pandas as pd

from . import __version__
from .schema import SCHEMA_VERSION, SOURCE_COLUMNS
from .transform import prepare_data, feature_engineering, validate_output


def project_root(start=None):
    """Find the project from any notebook directory, or use its installed location."""
    location = Path(start or Path.cwd()).resolve()
    for candidate in (location, *location.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "retail_etl").is_dir():
            return candidate
    return Path(__file__).resolve().parent.parent


def file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(value, path):
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_source(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path, dtype={"InvoiceNo": str, "StockCode": str,
                                         "CustomerID": str}, keep_default_na=False,
                             na_values=[""])
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype={"InvoiceNo": str, "StockCode": str,
            "CustomerID": str, "invoice_no": str, "stock_code": str, "customer_id": str},
            keep_default_na=False, na_values=[""])
    raise ValueError("Input must be .xlsx or .csv")


def run_pipeline(input_path=None, *, output_root=None, as_of=None, load_mysql=False):
    """Create an immutable run directory and publish latest.json only on success.

    CSV and MySQL cannot share a transaction. The manifest records a database
    publication independently if a subsequent local publication fails.
    """
    root = project_root()
    source = Path(input_path or root / "data/raw/Online Retail.xlsx").resolve()
    output = Path(output_root or root / "outputs").resolve()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:12]
    run_dir = output / "runs" / run_id
    run_dir.mkdir(parents=True)
    logger = logging.getLogger(f"retail_etl.{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = RotatingFileHandler(run_dir / "pipeline.log", maxBytes=2_000_000,
                                  backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    started = perf_counter()
    report = {"run_id": run_id, "pipeline_version": __version__,
              "schema_version": SCHEMA_VERSION, "status": "running",
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_file": source.name,
              "as_of": str(as_of or datetime.now(timezone.utc).date()),
              "database": {"status": "not_requested"}, "stage_seconds": {}}
    manifest = run_dir / "manifest.json"
    try:
        logger.info("Run %s started", run_id)
        atomic_json(report, manifest)
        stage_start = perf_counter()
        report["source_sha256"] = file_sha256(source)
        raw = read_source(source)
        if file_sha256(source) != report["source_sha256"]:
            raise ValueError("Source file changed during extraction")
        report["stage_seconds"]["extract"] = round(perf_counter() - stage_start, 3)
        logger.info("Extracted %s rows and %s columns", *raw.shape)
        stage_start = perf_counter()
        prepared = prepare_data(raw, as_of=report["as_of"])
        report["validation"] = prepared.validation
        prepared.rejected.to_csv(run_dir / "rejected_rows.csv", index=False)
        atomic_json(prepared.validation, run_dir / "validation.json")
        logger.info("Accepted %s rows; quarantined %s", len(prepared.cleaned), len(prepared.rejected))
        final = feature_engineering(prepared.cleaned)
        report["output_checks"] = validate_output(final)
        report["stage_seconds"]["transform_validate"] = round(perf_counter() - stage_start, 3)
        stage_start = perf_counter()
        prepared.cleaned.to_csv(run_dir / "cleaned_online_retail_data.csv", index=False,
                                date_format="%Y-%m-%d %H:%M:%S")
        final_path = run_dir / "feature_engineered_online_retail.csv"
        final.to_csv(final_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
        report["output_sha256"] = file_sha256(final_path)
        report["stage_seconds"]["export"] = round(perf_counter() - stage_start, 3)
        if load_mysql:
            from .database import publish_snapshot
            stage_start = perf_counter()
            report["database"] = {"status": "publishing"}
            atomic_json(report, manifest)
            report["database"] = publish_snapshot(final)
            report["stage_seconds"]["mysql"] = round(perf_counter() - stage_start, 3)
            atomic_json(report, manifest)
            logger.info("MySQL snapshot published; backup=%s", report["database"]["backup_table"])
        report.update(status="success", duration_seconds=round(perf_counter() - started, 3),
                      finished_at_utc=datetime.now(timezone.utc).isoformat())
        atomic_json(report, manifest)
        atomic_json({"run_id": run_id, "manifest": str(manifest.relative_to(output)),
                     "data": str(final_path.relative_to(output))}, output / "latest.json")
        logger.info("Run completed successfully")
        return report, final
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__,
                      duration_seconds=round(perf_counter() - started, 3),
                      finished_at_utc=datetime.now(timezone.utc).isoformat())
        logger.exception("Run failed")
        atomic_json(report, manifest)
        raise
    finally:
        handler.close()
        logger.removeHandler(handler)
