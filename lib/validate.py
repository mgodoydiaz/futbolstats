"""Data quality validation utilities.

Use `audit_parquet(path)` for a one-shot report on a single file, or
`audit_dir(dir)` to scan a folder. The functions return dicts so they can be
composed into longer reports.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .io import read_parquet


def audit_parquet(path: Path | str) -> dict[str, Any]:
    """Read a parquet file and return a quality report.

    Reports:
        - shape (rows, cols)
        - file size on disk (KB)
        - per-column NaN counts and rates
        - dtype distribution
        - all-null columns (likely scrape failures)
        - duplicate-row count
    """
    p = Path(path)
    df = read_parquet(p)
    size_kb = p.stat().st_size / 1024

    null_counts = df.isna().sum()
    null_rates = (null_counts / max(len(df), 1)).round(3)
    all_null = [c for c in df.columns if null_counts[c] == len(df)]
    high_null = [
        (c, float(null_rates[c]))
        for c in df.columns
        if 0.5 < null_rates[c] < 1.0
    ]
    dtype_counts = df.dtypes.astype(str).value_counts().to_dict()

    return {
        "path": str(p),
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "size_kb": round(size_kb, 1),
        "dtype_counts": dtype_counts,
        "all_null_cols": all_null,
        "high_null_cols": high_null,
        "duplicate_rows": int(df.duplicated().sum()),
    }


def audit_dir(root: Path | str, pattern: str = "*.parquet") -> list[dict[str, Any]]:
    """Audit every parquet under `root` matching `pattern`."""
    root = Path(root)
    return [audit_parquet(p) for p in sorted(root.rglob(pattern))]


def format_report(reports: list[dict[str, Any]]) -> str:
    """Format a list of audit dicts as a readable text report."""
    lines = []
    total_rows = sum(r["rows"] for r in reports)
    total_kb = sum(r["size_kb"] for r in reports)
    lines.append(f"# Data audit ({len(reports)} files)")
    lines.append("")
    lines.append(f"Total rows: {total_rows:,}")
    lines.append(f"Total size: {total_kb:,.1f} KB")
    lines.append("")
    lines.append("| File | Rows | Cols | KB | Dups | All-null cols | High-null cols |")
    lines.append("|------|-----:|-----:|---:|-----:|---------------|----------------|")
    for r in reports:
        name = Path(r["path"]).name
        all_null = ", ".join(r["all_null_cols"]) or "-"
        high_null = (
            ", ".join(f"{c}:{rate:.0%}" for c, rate in r["high_null_cols"]) or "-"
        )
        lines.append(
            f"| {name} | {r['rows']:,} | {r['cols']} | {r['size_kb']:.1f} | "
            f"{r['duplicate_rows']} | {all_null} | {high_null} |"
        )
    return "\n".join(lines)
