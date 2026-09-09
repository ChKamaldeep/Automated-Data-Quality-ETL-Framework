import json
import os
import subprocess
import sys

import pandas as pd
import pytest

from retail_etl.pipeline import run_pipeline, file_sha256
from retail_etl.transform import prepare_data, feature_engineering


def test_same_input_has_same_results_and_shared_functions(source, tmp_path):
    path = tmp_path / "raw.csv"
    source.to_csv(path, index=False)
    a, data = run_pipeline(path, output_root=tmp_path / "out", as_of="2011-12-09")
    b, again = run_pipeline(path, output_root=tmp_path / "out", as_of="2011-12-09")
    assert a["run_id"] != b["run_id"]
    assert a["output_sha256"] == b["output_sha256"]
    assert a["source_sha256"] == file_sha256(path)
    pd.testing.assert_frame_equal(data, again)
    pd.testing.assert_frame_equal(data, feature_engineering(prepare_data(source, as_of="2011-12-09").cleaned))
    assert json.loads((tmp_path / "out/latest.json").read_text())["run_id"] == b["run_id"]


def test_failed_run_preserves_previous_publication_and_logs_traceback(source, tmp_path):
    path = tmp_path / "raw.csv"
    source.to_csv(path, index=False)
    out = tmp_path / "out"
    run_pipeline(path, output_root=out, as_of="2011-12-09")
    latest = (out / "latest.json").read_bytes()
    with pytest.raises(FileNotFoundError):
        run_pipeline(tmp_path / "absent.csv", output_root=out, as_of="2011-12-09")
    assert (out / "latest.json").read_bytes() == latest
    manifests = [json.loads(p.read_text()) for p in out.glob("runs/*/manifest.json")]
    failed = next(m for m in manifests if m["status"] == "failed")
    log = (out / "runs" / failed["run_id"] / "pipeline.log").read_text()
    assert "Traceback" in log and "FileNotFoundError" in log


def test_cli_failure_returns_nonzero(tmp_path):
    result = subprocess.run([sys.executable, "-m", "retail_etl", "--input", str(tmp_path / "missing.csv"),
                             "--output-dir", str(tmp_path / "out")], capture_output=True, text=True)
    assert result.returncode == 1
    assert "ETL failed" in result.stderr


def test_all_rejected_is_failed_with_quarantine(source, tmp_path):
    path = tmp_path / "raw.csv"
    source["Quantity"] = 0
    source.to_csv(path, index=False)
    with pytest.raises(ValueError, match="empty"):
        run_pipeline(path, output_root=tmp_path / "out", as_of="2011-12-09")
    assert not (tmp_path / "out/latest.json").exists()
    rejected = next((tmp_path / "out").glob("runs/*/rejected_rows.csv"))
    assert len(pd.read_csv(rejected)) == len(source)
