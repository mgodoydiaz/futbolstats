# 07_features — Feature engineering

Scripts que transforman `01_data_raw/` (datos crudos del scraper) en tablas listas para ML en `02_data_processed/`.

## Scripts

| Script | Lee de | Escribe a | Qué hace |
|--------|--------|-----------|----------|
| `build_player_season.py` | `01_data_raw/players/fbref_<comp>_<stat>_<season>.parquet` | `02_data_processed/players_clean/fbref_<comp>_player_season.parquet` | Une las 5 stat types de FBref por (player, team, league, season). |

## Próximos scripts (pendientes)

- `build_player_match.py` — análogo a player_season pero a nivel partido (lee `01_data_raw/matches/fbref_*_summary_*.parquet`).
- `rolling_form.py` — para cada (player, match), agrega rolling mean/std de últimos N partidos.
- `opponent_adjusted.py` — divide stats por el promedio que el rival concede en esa stat.
- `per90_metrics.py` — normaliza counts por 90 minutos.

## Convenciones

- Suffix `__<stat_type>` en columnas para preservar la procedencia cuando se hace join multi-source.
- Identity cols (`player, team, league, season, nation, pos, age, born`) no llevan suffix.
- Una row = una unidad de observación del modelo (player-season, player-match, team-season, etc.).
- No usar `pd.merge(how='inner')` ciego — usa `how='outer'` y revisa NaNs después; perder filas a join es un bug.

## Cómo correr

```powershell
# Construye la tabla wide después de cada batch de scrapeo
python 07_features\build_player_season.py --comp Big5
```
