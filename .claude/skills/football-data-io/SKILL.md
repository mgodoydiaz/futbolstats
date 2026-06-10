---
name: football-data-io
description: Use when reading, writing, or designing storage for football stats data in this project. Enforces Parquet+zstd for tabular data, CSV only for entity catalogs in 03_entities/, and the lib.io module for all I/O. Trigger whenever data lands on disk or gets loaded back.
---

# Football data I/O

All tabular data in this project uses **Parquet with zstd compression (level 9)**. CSV is reserved for the 4 entity catalogs in `03_entities/`.

## Rules

1. **Never write raw CSV for stats data.** CSV is only for `03_entities/{players,teams,countries,competitions}.csv`.
2. **Always use `lib.io`** — never call `pd.to_parquet`/`pd.read_parquet`/`pd.to_csv` directly for project data:
   ```python
   from lib.io import read_parquet, write_parquet, read_entities, write_entities
   write_parquet(df, "01_data_raw/players/fbref_Big5_standard_2024-2025.parquet")
   df = read_parquet("01_data_raw/players/fbref_Big5_standard_2024-2025.parquet")
   countries = read_entities("countries")
   ```
3. **Path naming**: `01_data_raw/<entity>/<source>_<scope>_<stat>_<season>.parquet`
   - Examples:
     - `01_data_raw/players/fbref_Big5_standard_2024-2025.parquet`
     - `01_data_raw/players/fbref_PL_shooting_2023-2024.parquet`
     - `01_data_raw/matches/statsbomb_WorldCup_events_2022.parquet`
4. **Entity IDs** are prefixed by source: `fbref_d70ce98e`, `sb_11195`. Never use bare source IDs.

## Why Parquet + zstd

- ~5–10× smaller than CSV
- Preserves dtypes (no int → float silently on NaN)
- Column projection: `read_parquet(path, columns=["player_id","shots"])`
- Reads ~10–50× faster than CSV

## When to deviate

- **Raw API responses** (deeply nested JSON, HTML): cache verbatim in `01_data_raw/_cache/<source>/` — these are intermediate, not the canonical store.
- **Human-edited lookup tables**: CSV in `03_entities/`.
- **Narrative text**: Markdown in `04_history/`.

## Schemas

Documented in `lib/schemas.py`. Use `validate(df, schema)` for a sanity check (column presence only — does not enforce dtypes).

## Dtype hygiene before writing

Cast integer columns to smallest viable type before `write_parquet` — saves disk and memory:
- counts that fit 0–127: `Int8`
- counts that fit 0–32k (shots, passes per match): `Int16`
- season totals (minutes, total passes): `Int32`
- xG/xA continuous: `Float32` (rarely need Float64)
