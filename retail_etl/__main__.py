"""Command-line entry point: python -m retail_etl."""

import argparse
from datetime import date
import sys

from .pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Validate and publish the Online Retail sales snapshot")
    parser.add_argument("--input", help="Source .xlsx or .csv; defaults to the bundled UCI dataset")
    parser.add_argument("--output-dir", help="Output root; defaults to the repository outputs directory")
    parser.add_argument("--as-of", type=date.fromisoformat,
                        help="Inclusive source-calendar cutoff (YYYY-MM-DD); default: current UTC date")
    parser.add_argument("--load-mysql", action="store_true", help="Publish a verified MySQL snapshot")
    args = parser.parse_args()
    try:
        report, _ = run_pipeline(args.input, output_root=args.output_dir,
                                  as_of=args.as_of, load_mysql=args.load_mysql)
    except Exception as exc:
        # Connector error messages may contain connection details; the run log
        # retains the traceback. Never print environment variable values.
        print(f"ETL failed ({type(exc).__name__}). See the latest run directory's pipeline.log.", file=sys.stderr)
        return 1
    print(f"Success: {report['output_checks']['rows']:,} rows, "
          f"{report['output_checks']['columns']} columns. Run: {report['run_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
