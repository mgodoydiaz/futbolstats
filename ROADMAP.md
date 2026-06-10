# ROADMAP — Cargas pendientes y orden de ejecución

Cola priorizada de scrapes y post-procesado. Marca con `[x]` lo que vayas completando.

## Reglas de oro

- **Sólo UNA instancia FBref corriendo a la vez** (todas usan Chrome headless via soccerdata; concurrentes pelean por el caché).
- **StatsBomb es paralelo-safe** con FBref (usa GitHub raw, no browser).
- **Caché persistente**: re-correr el mismo comando es rápido (HTML cacheado en `01_data_raw/_cache/`). No tienes que tener miedo de interrumpir.
- **Cloudflare ocasional**: si ves `Could not retrieve page content within timeout`, soccerdata reintenta 5 veces. Si igual falla, esperá 10-15 min e intentá de nuevo (block temporal de IP).
- **Encoding en stdout**: si querés ver acentos correctamente, `$env:PYTHONIOENCODING='utf-8'` antes de correr. Los parquets SIEMPRE quedan bien (UTF-8).

## Estado actual (lo que ya está cargado)

- ✅ FBref Big 5 season aggregates, 5 temporadas (2020-21 a 2024-25): 25 parquets, 17,582 player-seasons en tabla wide.
- ✅ StatsBomb 4 competiciones: WC22, Euro24, La Liga 20-21 (Barça), PL 15-16 → 530 matches, 1.87M events, 15,109 player-match agregados.
- 🔄 **FBref PL 2024-25 match-level**: corriendo ahora en background. Output será `01_data_raw/matches/fbref_PL_summary_2024-2025.parquet`. ETA ~22:56.

---

## Fase A — Match-level current season para los 4 leagues restantes

**Prioridad ALTA**. Necesario para entrenar modelos de predicción de shots/tackles/fouls/cards por partido en cada liga.

**Tiempo total estimado: ~4-5 horas** (~60-70 min cada uno, secuencial obligatorio).

Encadenadas con `;` para correr seguido:

```powershell
python 06_ingestion\fbref_match_scraper.py --comp LL --season 2024-2025; `
python 06_ingestion\fbref_match_scraper.py --comp SA --season 2024-2025; `
python 06_ingestion\fbref_match_scraper.py --comp BL --season 2024-2025; `
python 06_ingestion\fbref_match_scraper.py --comp L1 --season 2024-2025
```

Checklist individual si las corrés sueltas:

- [ ] La Liga 2024-25 (`--comp LL`)
- [ ] Serie A 2024-25 (`--comp SA`)
- [ ] Bundesliga 2024-25 (`--comp BL`)
- [ ] Ligue 1 2024-25 (`--comp L1`)

**Lo que producís**: 4 parquets `fbref_<comp>_summary_2024-2025.parquet` con ~10-12k player-match rows cada uno.

---

## Fase B+ — Métricas expected y nuevas fuentes ✅ COMPLETA

Scripts y data nuevos:

- [x] **`07_features/build_discipline_setpieces.py`** — Agrega cards / fouls / corners / throw-ins / free kicks / goal kicks desde events StatsBomb.
  - Output: 18,961 player-match rows (`statsbomb_player_match_discipline.parquet`) + 1,816 team-match rows (`statsbomb_team_match_setpieces.parquet`).
  - Totales: 2,905 yellow / 46 second-yellow / 66 red; 9,018 corners; 40,482 throw-ins.

- [x] **`06_ingestion/understat_scraper.py`** — Scraper xG Big 5 vía Understat (sin Cloudflare).
  - Output: 5 parquets Big5 player-season (2020-2024), ~13,875 rows con `xg`, `np_xg`, `xa`, `xg_chain`, `xg_buildup`.
  - Llena el gap de xG que FBref vía soccerdata no entregaba.

- [x] **`06_ingestion/clubelo_scraper.py`** — Ratings Elo diarios por club.
  - Output: snapshot 630 clubs en `clubelo_snapshot_<date>.parquet`. Feature de strength del rival.

- [x] **`docs/`** — Tesis LaTeX 5 secciones: concepto xG, catálogo de métricas expected, fuentes, implementación, limitaciones.

- [x] **Skill `understat-ingest`** documentado en `.claude/skills/`.

**Pendiente de esta fase**: WhoScored (xCorners para Big 5 actual). Defer porque usa Chrome y choca con FBref scrapes.

---

## Fase B — StatsBomb expansión ✅ COMPLETA

5 competiciones nuevas cargadas (378 matches, 1.27M events):

- [x] Copa America 2024 (32 matches, 100k events)
- [x] UEFA Euro 2020 (51 matches, 193k events)
- [x] FIFA World Cup 2018 (64 matches, 228k events)
- [x] Women's World Cup 2019 + 2023 (116 matches, 403k events)
- [x] Indian Super League 2021-22 (115 matches, 345k events)

Total acumulado StatsBomb tras Phase B:
- 9 competiciones, 908 matches, ~3.1M events
- Player-match table: 26,295 rows (vs 15,109 antes)
- Catálogos: 14,566 jugadores (+2,257), 277 equipos (+62)

**Sub-fase opcional (B.5)**: MLS 2023 (~500 matches, ~1.5M events) si querés más volumen.

```powershell
# Si querés más competiciones después:
python 06_ingestion\statsbomb_loader.py --list   # ver qué hay
python 06_ingestion\statsbomb_loader.py -c "Major League Soccer" --season 2023
python 06_ingestion\statsbomb_aggregate.py        # re-rolls events
python 06_ingestion\statsbomb_entities.py         # +new players/teams
```

---

## Fase C — Temporadas históricas match-level

**Prioridad MEDIA**. Necesario para splits temporales (entrenar con T-1, validar con T).

**Tiempo: ~60-70 min cada (liga, temporada)**. Ideal para correr overnight.

Recomendado: 3 temporadas históricas mínimo por liga → 5 ligas × 3 = 15 jobs ≈ 16-18 horas.

```powershell
# 2023-24 todas las ligas (PL primero porque ya hay caché parcial si scrappiaste otra cosa)
python 06_ingestion\fbref_match_scraper.py --comp PL --season 2023-2024; `
python 06_ingestion\fbref_match_scraper.py --comp LL --season 2023-2024; `
python 06_ingestion\fbref_match_scraper.py --comp SA --season 2023-2024; `
python 06_ingestion\fbref_match_scraper.py --comp BL --season 2023-2024; `
python 06_ingestion\fbref_match_scraper.py --comp L1 --season 2023-2024

# 2022-23
python 06_ingestion\fbref_match_scraper.py --comp PL --season 2022-2023; `
python 06_ingestion\fbref_match_scraper.py --comp LL --season 2022-2023; `
python 06_ingestion\fbref_match_scraper.py --comp SA --season 2022-2023; `
python 06_ingestion\fbref_match_scraper.py --comp BL --season 2022-2023; `
python 06_ingestion\fbref_match_scraper.py --comp L1 --season 2022-2023

# 2021-22
python 06_ingestion\fbref_match_scraper.py --comp PL --season 2021-2022; `
python 06_ingestion\fbref_match_scraper.py --comp LL --season 2021-2022; `
python 06_ingestion\fbref_match_scraper.py --comp SA --season 2021-2022; `
python 06_ingestion\fbref_match_scraper.py --comp BL --season 2021-2022; `
python 06_ingestion\fbref_match_scraper.py --comp L1 --season 2021-2022
```

Checklist:

| Liga \ Temporada | 2023-24 | 2022-23 | 2021-22 | 2020-21 |
|------------------|:-------:|:-------:|:-------:|:-------:|
| Premier League   | [ ] | [ ] | [ ] | [ ] |
| La Liga          | [ ] | [ ] | [ ] | [ ] |
| Serie A          | [ ] | [ ] | [ ] | [ ] |
| Bundesliga       | [ ] | [ ] | [ ] | [ ] |
| Ligue 1          | [ ] | [ ] | [ ] | [ ] |

---

## Fase D — Post-procesado (después de cada batch grande)

Estas son **rápidas** (no usan red), pero deberías correrlas para mantener las tablas wide y los catálogos al día.

```powershell
# 1) Actualizar catálogos players.csv y teams.csv (idempotente)
python 06_ingestion\populate_entities.py

# 2) Si agregaste competiciones StatsBomb:
python 06_ingestion\statsbomb_aggregate.py

# 3) Tabla wide per-match por cada liga que tengas
python 07_features\build_player_match.py --comp PL
python 07_features\build_player_match.py --comp LL
python 07_features\build_player_match.py --comp SA
python 07_features\build_player_match.py --comp BL
python 07_features\build_player_match.py --comp L1

# 4) Tabla wide per-season
python 07_features\build_player_season.py --comp Big5

# 5) Audit completo
python 06_ingestion\validate_data.py --write 09_correlations\reports\audit.md
```

---

## Fase E — Modelado (cuando esté listo el match-level)

No es scraping, es lo que viene después. Pre-condición: al menos 2 temporadas completas de match-level en alguna liga.

- [ ] Replicar `08_models/shots_baseline.py` con XGBoost
- [ ] Feature engineering: `07_features/rolling_form.py`, `opponent_adjusted.py`, `days_rest.py`
- [ ] Un modelo por target: shots, passes_completed (StatsBomb), tackles, interceptions, fouls
- [ ] Splits temporales (T-1 train, T validate), nunca random shuffle
- [ ] Evaluación: MAE, RMSE, calibración vs baseline rolling-avg

---

## Inventario rápido de fuentes

| Fuente | Granularidad | Stats clave | Costo de scrape |
|--------|--------------|-------------|----------------|
| FBref season (Big5) | Player-season | goals, shots, SoT, cards, minutes, GK | ~30s por season |
| FBref match summary | Player-match | shots, SoT, tackles, interceptions, fouls, cards, crosses | ~11s por partido (Chrome) |
| StatsBomb events | Per-event | TODO (incluye passes, dribbles, xG por shot, freeze frame) | ~5-15 min por competición |

**Gap conocido**: passes/dribbles/possession **per match** no están en FBref vía soccerdata. Sólo vía StatsBomb donde haya cobertura.

---

## Tamaño esperado en disco al completar todo

| Etapa | Disco |
|-------|-------|
| Fase A (4 leagues match-level current season) | +120 MB cache + 1 MB parquet |
| Fase B (~3 comps StatsBomb extra) | +200-400 MB |
| Fase C (15 historical (liga, temporada)) | +450 MB cache + 5 MB parquet |
| **Total proyectado** | **~1.3 GB en `01_data_raw/_cache/`** |

El cache es regenerable y está en `.gitignore`. Los parquets finales son chicos (Parquet+zstd hace su magia).

---

## Si algo se rompe

- **403/429/CAPTCHA en FBref**: esperá 15-30 min. Cloudflare suelta el block.
- **soccerdata error parseando una tabla**: verificá que la versión sea `>= 1.9`. Si FBref cambió la página, soccerdata necesita update.
- **Parquet corrupto**: borralo y re-corré el scraper, regenera desde caché HTML en segundos.
- **Conflictos `players.csv` / `teams.csv`**: son idempotentes — re-correr `populate_entities.py` reconcilia.
- **Disco lleno**: `Remove-Item -Recurse '01_data_raw\_cache'` libera todo. Re-poblás cuando quieras.
