"""Walk 01_data_raw/ and 02_data_processed/ and print a quality audit report.

Usage:
    python 06_ingestion/validate_data.py
    python 06_ingestion/validate_data.py --dir 01_data_raw/players
    python 06_ingestion/validate_data.py --write 09_correlations/reports/audit.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.validate import audit_dir, format_report  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Audit parquet files in the project.")
    parser.add_argument(
        "--dir",
        action="append",
        default=None,
        help="Directory to scan (repeatable). Default: 01_data_raw and 02_data_processed.",
    )
    parser.add_argument(
        "--write",
        default=None,
        help="If given, write the report to this markdown path instead of stdout.",
    )
    args = parser.parse_args()

    dirs = args.dir or ["01_data_raw", "02_data_processed"]
    reports = []
    for d in dirs:
        p = PROJECT_ROOT / d
        if not p.exists():
            print(f"  (skip) {d} does not exist", file=sys.stderr)
            continue
        reports.extend(audit_dir(p))

    if not reports:
        print("No parquet files found.")
        return

    report = format_report(reports)
    if args.write:
        out = PROJECT_ROOT / args.write
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"Audit written to {out.relative_to(PROJECT_ROOT)}")
    else:
        print(report)


if __name__ == "__main__":
    main()
