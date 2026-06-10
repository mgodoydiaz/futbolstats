---
name: statsbomb-ingest
description: Use when ingesting StatsBomb Open Data (free event-level football data from https://github.com/statsbomb/open-data). Covers the loader/aggregator pair in 06_ingestion/, the StatsBomb data model (competitions -> seasons -> matches -> events -> lineups), event-type semantics, xG, ID conventions (sb_<id>), and required attribution. Trigger on anything StatsBomb-related: adding a new competition, debugging the aggregator, building new features off the events parquet.
---

# StatsBomb Open Data ingestion

## Attribution (required)

> Data provided by StatsBomb under their open data license.
> See https://github.com/statsbomb/open-data for terms.

This must appear in any user-facing surface that exposes derived stats.

## Data model

StatsBomb publishes everything as JSON on GitHub:

```
competitions.json                    # the catalog (one file)
matches/<competition_id>/<season_id>.json
events/<match_id>.json               # the big one — ~3000 rows per match
lineups/<match_id>.json
three-sixty/<match_id>.json          # tracking data (we don't pull this yet)
```

Conceptual hierarchy: **competition -> season -> match -> events (+ lineup)**.

We access it through the `statsbombpy` package (`pip install statsbombpy`).
The loader falls back to direct GitHub raw downloads if statsbombpy is missing.

## Scripts in this project

| File | Purpose |
|------|---------|
| `06_ingestion/statsbomb_loader.py` | CLI: download matches + events + lineups, persist as parquet under `01_data_raw/` |
| `06_ingestion/statsbomb_aggregate.py` | Roll events up to one row per (player, match), write `02_data_processed/events_clean/statsbomb_player_match.parquet` |

### Where files land

```
01_data_raw/_cache/statsbomb/                            # raw JSON cache (gitignored)
01_data_raw/matches/statsbomb_<CompSlug>_<season>.parquet
01_data_raw/events/statsbomb_<CompSlug>_<season>.parquet  # ~50-100 MB per major competition
01_data_raw/lineups/statsbomb_<CompSlug>_<season>.parquet
02_data_processed/events_clean/statsbomb_player_match.parquet
```

`<CompSlug>` is `slugify(competition_name)` — `'FIFA World Cup'` -> `'FIFAWorldCup'`.
`<season>` is `'2022'` for tournaments, `'2015-2016'` for league seasons.

### Loader CLI

```bash
# List everything available
python 06_ingestion/statsbomb_loader.py --list

# Substring match on competition name + year filter
python 06_ingestion/statsbomb_loader.py --competition "FIFA World Cup" --season 2022

# Multiple competitions in one run
python 06_ingestion/statsbomb_loader.py -c "UEFA Euro" -c "FIFA World Cup" --season 2024
```

The loader caches raw JSON in `01_data_raw/_cache/statsbomb/` (statsbombpy
respects `$STATSBOMBPY_CACHE_DIR` which the script sets before importing).
Re-runs are nearly free — only re-write the parquet from cache.

## Event types we care about (`event.type.name`)

StatsBomb's event taxonomy is rich. The ones that drive our ML targets:

| Type | Why it matters | Useful fields |
|------|----------------|---------------|
| `Pass` | Pass attempts/completions. **Completed = `pass_outcome` is NULL.** | `pass_outcome`, `pass_shot_assist`, `pass_goal_assist`, `pass_recipient`, `pass_length`, `pass_height` |
| `Shot` | Shots, xG, goals. | `shot_outcome`, `shot_statsbomb_xg`, `shot_body_part`, `shot_type`, `shot_freeze_frame` |
| `Dribble` | Take-ons. | `dribble_outcome` (`Complete` / `Incomplete`), `dribble_nutmeg` |
| `Duel` | **Tackles** live here — `type=Duel` AND `duel_type=Tackle`. Aerials too (`duel_type=Aerial Lost` is logged for the loser only). | `duel_type`, `duel_outcome` |
| `Interception` | Standalone event type — count directly. | `interception_outcome` |
| `Foul Committed` | Player committed a foul. | `foul_committed_type`, `foul_committed_card` |
| `Foul Won` | Foul drawn (by the player). | `foul_won_advantage`, `foul_won_defensive` |
| `Ball Recovery` | Loose-ball recovery (defensive contribution). | `ball_recovery_recovery_failure` |
| `Clearance` | Defensive clearance. | `clearance_body_part`, `clearance_aerial_won` |
| `Goal Keeper` | GK actions — shots faced, saves, claims, sweepers. | `goalkeeper_type`, `goalkeeper_outcome` |
| `Starting XI` | Per-team lineup snapshot at kickoff. **Used to compute minutes.** | `tactics.lineup` (JSON-serialized in our parquet) |
| `Substitution` | A player swap. Used for minutes calc — off player on `player_id`, on player on `substitution_replacement_id`. | `substitution_outcome`, `substitution_replacement_id` |
| `Half Start` / `Half End` | Period boundaries. We use the max `minute` per match as the final whistle. | — |

Other types we currently ignore: `Ball Receipt*`, `Carry`, `Pressure`,
`Block`, `Bad Behaviour`, `Miscontrol`, `Dispossessed`, `Dribbled Past`,
`Tactical Shift`, `Player Off`, `Player On`, `Injury Stoppage`, `Referee Ball-Drop`,
`Shield`, `Error`. Some of these (Pressure, Carry) are great inputs for richer
feature engineering — extend the aggregator when you need them.

## Shot outcomes & "on target"

`shot_outcome` enum: `Goal`, `Saved`, `Saved to Post`, `Saved Off Target`,
`Blocked`, `Off T`, `Post`, `Wayward`.

The aggregator counts as **on target**: `Goal`, `Saved`, `Saved to Post`,
`Saved Off Target`. `Blocked` is NOT on target (the ball was prevented from
ever reaching the keeper, by convention).

## xG (the crown jewel)

Every `Shot` event carries a pre-computed StatsBomb xG value in
`shot_statsbomb_xg` (Float). We sum these per (player, match) to get a
player's xG for that game. Headers, penalties, breakaways all get their own
realistic xG from StatsBomb's model — much better than self-rolled.

A typical match has 20-30 shots, total xG around 1.5-3.5 per team. If a
player has xG > 1.0 in one match it usually means a clear chance or two.

## Pass volume sanity

StatsBomb annotates carefully — they exclude things like throw-ins that other
providers count as passes. Typical totals per match:

- Each team: **~400-600 passes** in a tight knockout game.
- Each team: **~600-900 passes** in a possession-heavy league fixture.
- Combined per match: usually **800-1500 passes**.

If you see > 2000 combined, double-check your filter; if you see < 400,
suspect that not all events loaded.

## Minutes played

Computed in the aggregator from:
1. **Starters**: parsed from each team's `Starting XI` event (`tactics.lineup`
   — note the loader serialized this field as a JSON string).
2. **Subs in/out**: `Substitution` events. `player_id` = player going off,
   `substitution_replacement_id` = player coming on.
3. **Final whistle**: `max(events.minute)` per match (captures stoppage time).

Minutes for a player = `min(off_min, final_min) - on_min`. Players never on
the pitch get no row.

## Player & team IDs

Per project convention (`CLAUDE.md`):

- `player_id` = `"sb_" + <statsbomb_player_id>` (e.g. `sb_3500`)
- `team_id`   = `"sb_" + <statsbomb_team_id>`   (e.g. `sb_792`)
- `match_id`  = `"sb_" + <statsbomb_match_id>`

We also keep the raw int IDs in `player_id_sb` and `team_id_sb` for joins
back to the event data. Don't drop these.

Both the loader and aggregator write to `03_entities/players.csv` and
`03_entities/teams.csv` **as append-only** — they de-dupe on `player_id` so
fbref-sourced rows are safe from being clobbered.

## Output schema (`statsbomb_player_match.parquet`)

Matches `lib.schemas.PLAYER_MATCH_STATS` plus extras:

| Column | Type | Notes |
|--------|------|-------|
| `player_id`, `match_id`, `team_id`, `opponent_id`, `competition_id` | string | `sb_` prefixed |
| `season` | string | from `season_slug` — '2022' or '2015-2016' |
| `date` | string | ISO 8601 from `match_date` |
| `is_home` | boolean | |
| `minutes_played` | Int16 | derived |
| `goals`, `assists`, `shots`, `shots_on_target` | Int16 | |
| `xg` | Float32 | sum of `shot_statsbomb_xg` over the player's shots |
| `passes_attempted`, `passes_completed`, `key_passes` | Int16 | key_passes = `pass_shot_assist OR pass_goal_assist` |
| `dribbles_attempted`, `dribbles_completed` | Int16 | |
| `tackles` | Int16 | `Duel` with `duel_type=Tackle` |
| `interceptions` | Int16 | |
| `fouls_committed`, `fouls_drawn` | Int16 | |
| `player_name`, `team_name`, `competition_slug` | string | denormalized for convenience |
| `player_id_sb`, `team_id_sb` | Int64 | raw StatsBomb IDs |

The aggregator's `--mode replace` (default) drops existing rows that match the
incoming `(competition_slug, season)` keys before appending — so re-runs are
idempotent. Use `--mode append` to skip the dedup.

## Extending the pipeline

Add an event type or new derived stat:

1. In `statsbomb_aggregate.py`, add a row-level boolean (e.g. `is_press = df['type'] == 'Pressure'`).
2. Add the count column to `df['my_new_stat'] = is_press.astype('int16')`.
3. Add to `agg_cols` list.
4. Add to `int_cols` for dtype shrinking.
5. Add to the `preferred` ordered list at the bottom.
6. Re-run on a known competition and spot-check the values.

Add a new competition to load:

1. `python 06_ingestion/statsbomb_loader.py --list | grep -i <name>`
2. Pick the `competition_id` and `season_id` (or use a name substring).
3. Run the loader, then the aggregator (without --file to refresh everything).

## Performance / footprint

- A WC-sized competition (64 matches): ~200k events, ~50-80 MB parquet (zstd-9).
- statsbombpy is single-threaded by default but caches aggressively; first
  download of a competition is the slow part (a couple of minutes), re-runs
  are seconds.
- The aggregator is in-memory — loads each events parquet whole. For
  league-season parquets (380+ matches) keep an eye on RAM; consider
  iterating per-match if it ever exceeds a few GB.
