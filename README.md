# Futbolstats

Sistema de análisis estadístico de fútbol. Objetivo: encontrar correlaciones y **predecir estadísticas individuales** (tiros, pases, xG, asistencias) mediante machine learning — no predecir resultados.

## Estructura

| Carpeta | Contenido | Formato |
|---------|-----------|---------|
| `01_data_raw/` | Datos crudos sin procesar | Parquet + caché HTML |
| `02_data_processed/` | Datos limpios y normalizados | Parquet |
| `03_entities/` | Catálogos maestros (IDs canónicos) | CSV |
| `04_history/` | Narrativas y contexto cualitativo | Markdown |
| `05_playstyle/` | Clasificaciones de estilos de juego | Parquet + Markdown |
| `06_ingestion/` | Scripts de scraping y APIs | Python |
| `07_features/` | Feature engineering | Python |
| `08_models/` | Modelos de ML | Python + Parquet |
| `09_correlations/` | Análisis exploratorio | Jupyter |
| `10_serving/` | Outputs consumibles | — |
| `lib/` | Utilidades compartidas (I/O, schemas) | Python |

## Formato de almacenamiento

- **Parquet con compresión zstd nivel 9** para todo dato tabular. Aproximadamente 5–10× más pequeño que CSV y conserva dtypes.
- **CSV** solo para los 4 catálogos de `03_entities/` (editables a mano).
- **Markdown** para contexto cualitativo en `04_history/`.

## Instalación

**Recomendado: conda** (todo el stack científico viene pre-compilado):

```powershell
conda env create -f environment.yml
conda activate futbolstats
```

**Alternativa: venv + pip**:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso básico

```python
from lib.io import read_parquet, write_parquet

df = read_parquet("01_data_raw/players/fbref_Big5_standard_2024-2025.parquet")
```

Scrapear estadísticas Big 5:

```powershell
python 06_ingestion\fbref_scraper.py --comp Big5 --stat standard --season 2024-2025
python 06_ingestion\fbref_scraper.py --comp Big5 --all-stats --season 2024-2025
```

## Pipeline de apuestas (player props)

Capa que conecta las predicciones con las cuotas para detectar apuestas de valor
esperado positivo. Convierte **predicción → probabilidad → EV vs cuota → Kelly**.

```powershell
# 1. construir la vista de partidos (fixtures, predicciones, EV) con odds sintéticas
python 07_features\build_matches_view.py --source statsbomb --synthetic

# 2. backtest de la lógica (ROI por threshold, calibración, drawdown)
python 08_models\backtest_betting.py

# 3. analizar interactivo
jupyter lab 09_correlations\notebooks\01_match_betting.ipynb

# 4. cuotas reales de Pinnacle (fútbol: sólo goles y tarjetas)
python 06_ingestion\pinnacle_scraper.py --list-leagues
```

Piezas: [`lib/betting.py`](lib/betting.py) (odds, vig, Poisson/NegBin O/U, EV, Kelly +
tests), [`lib/backtest.py`](lib/backtest.py), [`07_features/build_matches_view.py`](07_features/build_matches_view.py),
[`06_ingestion/pinnacle_scraper.py`](06_ingestion/pinnacle_scraper.py). Guía completa en
[`09_correlations/notebooks/README.md`](09_correlations/notebooks/README.md).

> ⚠️ Análisis estadístico personal, no asesoría de apuestas. El backtest sintético
> valida la *lógica*, no promete edge real. Apostar arriesga pérdida total.

## Stack

- **`soccerdata`** para FBref (Cloudflare JS challenge → SeleniumBase + Chrome headless).
- **`statsbombpy`** para StatsBomb Open Data (JSON desde GitHub, sin scraping).
- **`pyarrow`** para Parquet con zstd nivel 9.
- **`pandas`** para manipulación tabular.

## Estado de la base de datos

### Datos cargados

**FBref Big 5 (5 ligas, 5 temporadas: 2020-21 a 2024-25)**
- 25 parquets stat-type × temporada en `01_data_raw/players/`
- Total: 61,647 player-season rows raw
- Tabla wide (joined): `02_data_processed/players_clean/fbref_Big5_player_season.parquet` — **17,582 filas × 85 cols** (5 ligas, 5 temporadas)
- Stat types cubiertos: `standard`, `shooting`, `playing_time`, `misc`, `keeper`

**FBref per-match (PL 2024-25, en progreso)**
- Pilot validado (5 matches × 28 cols)
- Full scrape corriendo (~66 min para 380 matches)
- Output esperado: `01_data_raw/matches/fbref_PL_summary_2024-2025.parquet`

**StatsBomb (eventos detallados)**
- 4 competiciones cargadas: WC 2022, Euro 2024, La Liga 2020-21 (Barça), PL 2015-16
- 530 matches, 1.87M events (en `01_data_raw/events/`)
- Tabla agregada per-player-per-match: `02_data_processed/events_clean/statsbomb_player_match.parquet` — **15,109 filas × 28 cols** (incluye passes_completed/attempted, dribbles, tackles, xG)

**Entidades**
- 62 países, 21 competiciones (seeds)
- 12,309 jugadores (fbref + sb), 215 equipos

**Total**: 41 parquet files, ~2M rows, ~129 MB en disco.

### Para cargar más data

```powershell
# Más temporadas FBref:
python 06_ingestion\fbref_scraper.py --comp Big5 --all-stats --seasons 2015-2016,2016-2017

# Más ligas/temporadas a nivel partido (warning: ~66 min por liga-temporada):
python 06_ingestion\fbref_match_scraper.py --comp LL --season 2024-2025
python 06_ingestion\fbref_match_scraper.py --comp SA --season 2024-2025

# Más competiciones StatsBomb:
python 06_ingestion\statsbomb_loader.py --list      # ver disponibles
python 06_ingestion\statsbomb_loader.py --competition "FIFA Women's World Cup"

# Después de cada carga:
python 06_ingestion\populate_entities.py
python 07_features\build_player_season.py --comp Big5
python 06_ingestion\validate_data.py --write 09_correlations\reports\audit.md
```

### Próximas fases

2. **Match-level expansion** — scrapear las otras 4 ligas Big 5 + más temporadas históricas.
3. **Feature engineering** — rolling form, opponent-adjusted, days_rest (`07_features/`).
4. **Modelos baseline** — XGBoost por target (passes, shots, tackles) en `08_models/`.
5. **Análisis de correlaciones** — matrices, PCA, mutual info (`09_correlations/`).

## Fases siguientes

2. Stats core por jugador/partido (eventos detallados, posiblemente StatsBomb Open Data)
3. Estilo de juego cuantificado (clustering de arquetipos)
4. Modelos predictivos de estadísticas (XGBoost, modelos jerárquicos)
5. Análisis de correlaciones (matrices, PCA, mutual information)
