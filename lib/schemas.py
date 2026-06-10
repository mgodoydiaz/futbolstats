"""Schema definitions for entity catalogs and core stats tables.

Each schema is a dict mapping column name → pandas/pyarrow dtype string.
These are documentation + validation contracts, not enforced at write-time.
Use `validate(df, schema)` to check a DataFrame against a schema.
"""
from __future__ import annotations

import pandas as pd

# --------------------------------------------------------------------------
# Entity catalogs (stored as CSV in 03_entities/)
# --------------------------------------------------------------------------

PLAYERS = {
    "player_id":        "string",   # canonical: <source>_<source_id>
    "name":             "string",   # full name as in source
    "name_normalized":  "string",   # lowercase, no accents (lib.text.normalize)
    "birth_date":       "string",   # ISO 8601 YYYY-MM-DD
    "nationality":      "string",   # ISO 3166-1 alpha-3
    "position":         "string",   # GK | DF | MF | FW (primary)
    "foot":             "string",   # L | R | B
    "height_cm":        "Int16",
    "weight_kg":        "Int16",
    "source":           "string",   # fbref | statsbomb | transfermarkt | ...
    "source_id":        "string",
}

TEAMS = {
    "team_id":          "string",
    "name":             "string",
    "name_normalized":  "string",
    "country":          "string",   # ISO alpha-3
    "founded_year":     "Int16",
    "stadium":          "string",
    "source":           "string",
    "source_id":        "string",
}

COUNTRIES = {
    "country_id":       "string",   # ISO 3166-1 alpha-3
    "name":             "string",
    "confederation":    "string",   # UEFA | CONMEBOL | CONCACAF | AFC | CAF | OFC
}

COMPETITIONS = {
    "competition_id":   "string",   # <source>_<source_id>
    "name":             "string",
    "country":          "string",   # ISO alpha-3, or INT for international
    "tier":             "Int8",     # 1 = top division
    "format":           "string",   # league | cup | group_knockout
    "source":           "string",
    "source_id":        "string",
}

# --------------------------------------------------------------------------
# Stats tables (stored as Parquet in 01_data_raw/ and 02_data_processed/)
# --------------------------------------------------------------------------

# Per-player, per-season aggregate (what FBref's "standard" table looks like)
PLAYER_SEASON_STATS = {
    "player_id":        "string",
    "team_id":          "string",
    "competition_id":   "string",
    "season":           "string",   # e.g. "2024-2025"
    "minutes":          "Int32",
    "matches":          "Int16",
    "starts":           "Int16",
    "goals":            "Int16",
    "assists":          "Int16",
    "shots":            "Int32",
    "shots_on_target":  "Int32",
    "xg":               "Float32",
    "xa":               "Float32",
    "passes_completed": "Int32",
    "passes_attempted": "Int32",
    "key_passes":       "Int32",
    "dribbles":         "Int32",
    "tackles":          "Int32",
    "interceptions":    "Int32",
    "yellow_cards":     "Int16",
    "red_cards":        "Int16",
}

# Per-player, per-match (richer — populated from event-level sources)
PLAYER_MATCH_STATS = {
    "player_id":        "string",
    "match_id":         "string",
    "team_id":          "string",
    "opponent_id":      "string",
    "competition_id":   "string",
    "season":           "string",
    "date":             "string",   # ISO 8601 YYYY-MM-DD
    "is_home":          "boolean",
    "minutes":          "Int16",
    "goals":            "Int8",
    "assists":          "Int8",
    "shots":            "Int8",
    "shots_on_target":  "Int8",
    "xg":               "Float32",
    "xa":               "Float32",
    "passes_completed": "Int16",
    "passes_attempted": "Int16",
    "key_passes":       "Int8",
    "dribbles":         "Int8",
    "tackles":          "Int8",
    "interceptions":    "Int8",
}


def validate(df: pd.DataFrame, schema: dict) -> list[str]:
    """Return a list of mismatch descriptions. Empty list = schema OK.

    Checks that columns exist; does not enforce dtypes (cast yourself if needed).
    Extra columns in `df` are allowed (not flagged).
    """
    issues: list[str] = []
    for col in schema:
        if col not in df.columns:
            issues.append(f"missing column: {col}")
    return issues
