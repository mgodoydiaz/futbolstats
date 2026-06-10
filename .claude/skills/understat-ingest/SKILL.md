---
name: understat-ingest
description: Use when ingesting data from Understat (https://understat.com). Understat is a free shot-level data source covering Big 5 European leagues + Russian Premier League from 2014 onwards. No Cloudflare; plain HTTP scraping via soccerdata.Understat. Trigger on any task involving Understat scraping, debugging the Understat scraper, or extending coverage.
---

# Understat ingestion

## When to use Understat (not FBref / not StatsBomb)

- Need **xG aggregated per player-season** for Big 5 leagues, multiple seasons. FBref Big5 combined doesn't expose the Expected supergroup; Understat does, natively.
- Need **per-shot xG with coordinates** for a Big 5 game (continuous coverage, unlike StatsBomb's sparse competition list).
- Want a second xG estimate to cross-validate StatsBomb's model.

## When NOT to use Understat

- Need passes/dribbles/defensive events with detail → use StatsBomb events.
- Need season totals beyond xG-related stats (cards, tackles, fouls) → use FBref aggregates.
- Need leagues outside Big 5 + RFPL.

## Stack

soccerdata wraps Understat with **plain HTTP** (no Selenium / no Chromium). Free of Cloudflare. Caching goes under `01_data_raw/_cache/soccerdata/data/Understat/`.

```python
import soccerdata as sd
us = sd.Understat(leagues=["ENG-Premier League"], seasons="2024")
df_season = us.read_player_season_stats()
df_match  = us.read_player_match_stats()
df_shots  = us.read_shot_events()
df_sched  = us.read_schedule()
```

## Season format

Understat seasons are encoded as the **starting year**: `2024` = 2024-2025, `2014` = 2014-2015. Don't pass `"2024-2025"`, pass `"2024"` (or int 2024).

## Available leagues (soccerdata mapping)

| Shortcut | soccerdata key |
|----------|----------------|
| `Big5` | All five top leagues |
| `PL` | `ENG-Premier League` |
| `LL` | `ESP-La Liga` |
| `SA` | `ITA-Serie A` |
| `BL` | `GER-Bundesliga` |
| `L1` | `FRA-Ligue 1` |
| `RU` | `RUS-Premier League` |

Coverage starts at season 2014 (year-format).

## Output schema (player_season_stats)

Columns we get back after `reset_index()` + flatten:

```
league, season, team, player, league_id, season_id, team_id, player_id,
position, matches, minutes, goals, xg, np_goals, np_xg, assists, xa,
shots, key_passes, yellow_cards, red_cards, xg_chain, xg_buildup
```

Key xG-derived columns:
- `xg`, `np_xg` — total / non-penalty expected goals
- `xa` — expected assists
- `xg_chain` — sum of xG of possessions the player was involved in
- `xg_buildup` — same but excluding shots and key passes of the player (pure buildup contribution)

## Player IDs

Understat exposes its own integer `player_id`. Use prefix `us_<id>` when adding to the canonical catalog. Cross-source matching against `fbref_*` and `sb_*` IDs requires name normalization (`lib.text.normalize_name`).

## Comparison with StatsBomb xG

Understat's xG model uses **only shot-level features** (location, body part, type of play). StatsBomb's model uses **freeze-frame** (positions of all players, goalkeeper position). Therefore:

- For the same shot, Understat and StatsBomb xG values differ.
- For a player's season total xG across Big 5, both should rank players similarly but the exact values diverge by ~10-20%.
- For analysis: **use one source consistently**. Don't mix per-shot xG values from both in the same model.

## Project scripts

- `06_ingestion/understat_scraper.py` — CLI scraper. Outputs `01_data_raw/players/understat_<comp>_player_<stat>_<season>.parquet`.

## Speed

~30 seconds per (league, season) on first fetch. Cached afterwards. No rate limiting in practice.
