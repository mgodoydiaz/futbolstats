# Futbolstats — guía para Claude

Sistema de análisis estadístico de fútbol. La meta es **predecir estadísticas individuales** (tiros, pases, xG, asistencias) — no predecir resultados de partidos. Modelos = regresión sobre métricas continuas, no clasificación de W/L/D.

## Reglas de almacenamiento

- **Datos tabulares → Parquet con zstd (nivel 9)**. Nunca escribir CSV para stats.
- **Entidades pequeñas (catálogos) → CSV** en `03_entities/` únicamente. Son editables a mano.
- **Texto narrativo → Markdown** en `04_history/`.
- **Cache de HTML/JSON crudo** → `01_data_raw/_cache/<source>/` (gitignored).

## I/O: usa siempre `lib.io`

```python
from lib.io import read_parquet, write_parquet, read_entities

df = read_parquet("01_data_raw/players/fbref_Big5_standard_2024-2025.parquet")
write_parquet(df, "02_data_processed/players_clean/big5_2024.parquet")
players_catalog = read_entities("players")
```

No uses `pd.to_parquet()` ni `pd.to_csv()` directamente para datos del proyecto — perderás la convención de compresión.

## Convención de IDs

- Player ID: `<source>_<source_id>` → `fbref_d70ce98e`, `sb_11195`.
- Team ID: `<source>_<source_id>` → `fbref_18bb7c10`.
- Country ID: ISO 3166-1 alpha-3 → `ARG`, `BRA`, `ESP`.
- Competition ID: `<source>_<source_id>` → `fbref_9`.

Nunca uses el source_id pelado — siempre con prefijo. Esto permite cruzar datos de múltiples fuentes después.

## Naming de archivos parquet

`<source>_<scope>_<stat>_<season>.parquet`

Ejemplos:
- `fbref_Big5_standard_2024-2025.parquet`
- `fbref_PL_shooting_2023-2024.parquet`
- `statsbomb_WorldCup_events_2022.parquet`

## Reglas por fuente

### Understat
- HTTP simple, sin Cloudflare. soccerdata `sd.Understat()` lo wrappea.
- Cubre Big 5 + RFPL desde 2014.
- Provee xG, npxG, xA, xg_chain, xg_buildup a nivel season y match. Llena el gap de xG que tiene FBref Big5 via soccerdata.
- Season format: año de inicio como string. `"2024"` = 2024-2025.
- Ver skill `understat-ingest`.

### ClubElo
- API simple HTTP, instantáneo.
- `read_by_date(date)` = snapshot de todos los clubes europeos.
- `read_team_history(team)` = histórico diario por club.
- Usar como feature de "strength of opponent" en modelos jugador-partido.

### FBref
- FBref está detrás de Cloudflare JS challenge (`cf-mitigated: challenge`) — `requests` y `curl_cffi` reciben 403.
- Usamos **`soccerdata`** que levanta Chrome headless vía SeleniumBase y resuelve el challenge.
- HTML cacheado en `01_data_raw/_cache/soccerdata/data/FBref/`. Re-runs son casi instantáneas. Borrar archivo para forzar refresh.
- Columns vienen como MultiIndex — el scraper aplana a `Top_Bottom`.
- Row index (`league, season, team, player`) se mueve a columnas vía `reset_index()`.
- Ver skill `fbref-ingest` para detalles.

## Mapa de carpetas

| Path | Propósito |
|------|-----------|
| `01_data_raw/` | Datos sin procesar (parquet + caché HTML) |
| `02_data_processed/` | Limpios, normalizados, joineados |
| `03_entities/` | Catálogos maestros (CSV) |
| `04_history/` | Contexto cualitativo (markdown) |
| `05_playstyle/` | Clasificaciones de estilo |
| `06_ingestion/` | Scrapers y clientes API |
| `07_features/` | Feature engineering |
| `08_models/` | Modelos de ML |
| `09_correlations/` | EDA (notebooks) |
| `10_serving/` | Outputs |
| `lib/` | Utilidades compartidas |

## Filosofía de modelado

- **Targets son continuos**: shots, shots_on_target, passes_completed, xG, xA, dribbles, tackles.
- **Features clave**: rolling form (últimos 5/10 partidos), ajustado por nivel de rival, local/visitante, descanso, compañeros en cancha, embeddings de player_id y team_id.
- **Modelos baseline**: XGBoost/LightGBM por target.
- **Modelos avanzados**: jerárquicos bayesianos (PyMC) para capturar efectos jugador+equipo+rival; redes con embeddings.
- Evaluar con MAE / RMSE / calibración, no accuracy.

## Fuentes y qué stat types nos da cada una

### FBref (vía soccerdata 1.9)
- **Season aggregates** (`fbref_scraper.py`): 5 stat types — `standard`, `shooting`, `playing_time`, `misc`, `keeper`. soccerdata NO expone passing/defense/possession a nivel temporada.
- **Per-match player stats** (`fbref_match_scraper.py`): `stat_type='summary'` da el view consolidado por partido con **shots, SoT, xG, xA, passes, key passes, tackles, interceptions, blocks, dribbles, fouls, cards**. Una HTTP request por partido (~3s rate limit).
- Cobertura: ligas top, ~5 temporadas viable.

### StatsBomb Open Data (vía statsbombpy)
- Event-level detalle (cada pase, tiro, dribble, duelo) → aggregable a per-player-per-match con **mucho más detalle** que FBref summary.
- Cobertura limitada: WC 2022, Euro 2024, Champions finals, carrera Messi (Argentina + Barça), etc.
- Usar para ground-truth de stats que FBref no provee fácilmente.

### Combinación
- Para predicción de stats de Big 5 actual → FBref match-level es la fuente primaria.
- Para validar features (xG, presión, etc.) → StatsBomb donde hay overlap.
- `02_data_processed/players_clean/fbref_<comp>_player_season.parquet` une las 5 stat types de FBref por (player, team, league, season).

## Skills disponibles en este proyecto

Las skills locales en `.claude/skills/` se cargan automáticamente. Las relevantes:

- `football-data-io` — convenciones de I/O.
- `fbref-ingest` — quirks de scraping FBref.

## Pythonismos del proyecto

- Los scripts en carpetas numeradas (`06_ingestion/`, etc.) **no son paquetes importables** — el nombre no puede empezar con dígito. Se ejecutan como scripts standalone. Acceden a `lib/` agregando el project root a `sys.path`:
  ```python
  PROJECT_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(PROJECT_ROOT))
  from lib.io import write_parquet
  ```
- Solo `lib/` es paquete importable.
