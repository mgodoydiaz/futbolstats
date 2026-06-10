---
name: fbref-ingest
description: Use when ingesting data from FBref.com. FBref enabled Cloudflare JS challenge in 2024 — plain requests/curl_cffi return 403. This skill enforces the soccerdata wrapper (headless Chrome via SeleniumBase), the project's cache layout, and the column-flattening contract. Trigger on any FBref scrape, debug, or new endpoint.
---

# FBref ingestion

## Why soccerdata (not raw requests)

FBref sits behind Cloudflare's **JS challenge** mode (`cf-mitigated: challenge`). Plain `requests` and `curl_cffi` both return 403. The only reliable path is a real browser, which `soccerdata` provides via SeleniumBase (bundled Chrome driver).

Use the wrapper. Don't try to roll a raw scraper.

## Standard pattern

```python
import os, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault(
    "SOCCERDATA_DIR",
    str(PROJECT_ROOT / "01_data_raw" / "_cache" / "soccerdata"),
)

import soccerdata as sd
from lib.io import write_parquet

fb = sd.FBref(leagues="Big 5 European Leagues Combined", seasons="2024-2025")
df = fb.read_player_season_stats(stat_type="standard")
df = df.reset_index()     # league, season, team, player → columns
# flatten MultiIndex columns, then write_parquet(df, ...)
```

The `SOCCERDATA_DIR` env var **must be set before importing soccerdata** — that's why the line goes above the import. Without it, caches go to `%LOCALAPPDATA%\soccerdata` outside the project.

## Known data gaps

- **xG / npxG missing from Big5 shooting**: the soccerdata-fetched HTML for `Big 5 European Leagues Combined / shooting` only contains the Standard supergroup (Sh, SoT, etc.). The Expected supergroup (xG, npxG, xG/Sh, G-xG) is absent. Verified by inspecting cached HTML. To get aggregate xG: either compute from StatsBomb events where available, or scrape single-league shooting pages directly (which may include Expected).
- **Bundesliga rows arrive with `league = NaN`**: soccerdata bug. Patched in `07_features/build_player_season.py` by mapping via team membership and falling back to literal `"GER-Bundesliga"`.
- **Per-match `summary` only contains the Performance block**: passes, dribbles, possession not included per match from FBref. Use StatsBomb's `02_data_processed/events_clean/statsbomb_player_match.parquet` for those columns where competition overlap exists.

## Stat types — what soccerdata 1.9 actually exposes

Don't assume FBref's full set is available. The wrapper has explicit allow-lists per method:

| Method | Valid stat_types |
|--------|------------------|
| `read_player_season_stats` | `standard`, `keeper`, `shooting`, `playing_time`, `misc` |
| `read_team_season_stats` | `standard`, `keeper`, `shooting`, `playing_time`, `misc` |
| `read_team_match_stats` | `schedule`, `shooting`, `keeper`, `misc` |
| `read_player_match_stats` | `summary`, `keepers` |

**Where passing / defense / possession / GCA detail comes from:**
- Per-season aggregates: NOT available via soccerdata. Would require custom scraping or different source.
- Per-match player level: USE `read_player_match_stats(stat_type='summary')` — its 'summary' table is FBref's consolidated per-match view that includes passes, key passes, tackles, interceptions, blocks, dribbles, fouls, cards, plus shots/xG/xA.

So our pipeline is:
- Season-aggregate stats: `fbref_scraper.py` (5 stat types)
- Per-match player stats: `fbref_match_scraper.py` (`summary`) — much richer per row
- Passes / defense / possession from open events: StatsBomb (`statsbomb_*.py`, limited to specific competitions)

## League keys

soccerdata uses long names, not codes. The scraper maps our shortcuts:

| Shortcut | soccerdata key |
|----------|----------------|
| `Big5` | `Big 5 European Leagues Combined` |
| `PL`   | `ENG-Premier League` |
| `LL`   | `ESP-La Liga` |
| `SA`   | `ITA-Serie A` |
| `BL`   | `GER-Bundesliga` |
| `L1`   | `FRA-Ligue 1` |

## Output shape

After `read_player_season_stats` + `reset_index` + flatten:

| Column type | Examples |
|-------------|----------|
| Identity | `league`, `season`, `team`, `player`, `nation`, `pos`, `age`, `born` |
| Playing time | `Playing Time_MP`, `Playing Time_Starts`, `Playing Time_Min`, `Playing Time_90s` |
| Performance | `Performance_Gls`, `Performance_Ast`, `Performance_CrdY`, `Performance_CrdR` |
| Per 90 | `Per 90 Minutes_Gls`, `Per 90 Minutes_Ast`, ... |

Other `stat_type` values produce different column sets — inspect `df.columns` first.

## Performance notes

- First fetch: ~30–60 s (browser cold start + Cloudflare challenge).
- Subsequent fetches: HTML cached, near-instant (read from `01_data_raw/_cache/soccerdata/data/FBref/`).
- Delete the matching file in the cache to force re-fetch.

## Player IDs

soccerdata strips the FBref player_id by default. To map a player back to FBref:
- `read_player_match_stats` returns rows keyed by team+player+date.
- For canonical `player_id`, use `fb.read_team_season_stats()` plus the player-page scrape (not in MVP yet).

For now, the player **name + team + season** is the de-facto join key. Real `fbref_<id>` mapping is Phase 2 work.

## Encoding gotcha (Windows)

Player names contain accents (Mbappé, Doué, Müller). Parquet stores UTF-8 fine, but Python's default stdout in PowerShell uses cp1252 — `print(df)` may show `?` or crash with `UnicodeEncodeError`. Workarounds:
- `set PYTHONIOENCODING=utf-8` in the shell
- Or just inspect the data in a notebook / write to file instead of printing
