"""I/O utilities for Futbolstats.

Convention enforced project-wide:
    - Tabular stats data → Parquet with zstd level 9 (compact, fast, dtype-safe).
    - Entity catalogs (small lookup tables) → CSV in `03_entities/`.

Always import from here instead of calling `pd.to_parquet` or `pd.read_csv`
directly so the project's compression and path conventions stay consistent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Union

import pandas as pd

PathLike = Union[str, Path]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENTITIES_DIR = PROJECT_ROOT / "03_entities"

PARQUET_COMPRESSION = "zstd"
PARQUET_COMPRESSION_LEVEL = 9


def _resolve(path: PathLike) -> Path:
    """Resolve `path` against the project root if it's relative."""
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def write_parquet(df: pd.DataFrame, path: PathLike) -> Path:
    """Write a DataFrame to Parquet with zstd compression (level 9).

    Creates parent directories as needed. Returns the absolute path written.
    """
    out = _resolve(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(
        out,
        engine="pyarrow",
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        index=False,
    )
    return out


def read_parquet(
    path: PathLike,
    columns: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Read a Parquet file. Pass `columns` to project only specific columns."""
    return pd.read_parquet(
        _resolve(path),
        engine="pyarrow",
        columns=list(columns) if columns is not None else None,
    )


def read_entities(name: str) -> pd.DataFrame:
    """Read an entity CSV from `03_entities/<name>.csv`.

    Valid names: `players`, `teams`, `countries`, `competitions`.
    """
    path = ENTITIES_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Entity catalog not found: {path}")
    return pd.read_csv(path, dtype="string")


def write_entities(df: pd.DataFrame, name: str) -> Path:
    """Write/overwrite an entity catalog in `03_entities/<name>.csv`.

    CSV (not parquet) so humans can edit them manually.
    """
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    path = ENTITIES_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    return path
