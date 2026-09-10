import json
from pathlib import Path

from retail_etl.schema import create_table_sql

ROOT = Path(__file__).resolve().parents[1]


def test_documented_ddl_matches_authoritative_contract():
    script = (ROOT / "sql/mysql_load/02_create_table.sql").read_text()
    assert create_table_sql(if_not_exists=True) + ";" in script


def test_notebooks_execute_with_shared_logic(source, tmp_path, monkeypatch):
    """Execute every code cell sequentially on a small source, without live DB writes."""
    path = tmp_path / "source.csv"
    source.to_csv(path, index=False)
    monkeypatch.setenv("RETAIL_ETL_INPUT", str(path))
    monkeypatch.setenv("RETAIL_ETL_OUTPUT", str(tmp_path / "out"))
    monkeypatch.chdir(ROOT / "notebooks")
    import nbformat
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        namespace = {"__name__": "__main__"}
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == "code":
                exec(compile(cell.source, f"{path.name}:cell{i}", "exec"), namespace)
