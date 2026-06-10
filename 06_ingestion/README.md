# 06_ingestion — Scrapers y clientes API

Scripts standalone que descargan datos crudos. **No son paquetes importables** (la carpeta empieza con dígito). Se corren así:

```powershell
python 06_ingestion\fbref_scraper.py --help
```

## Fuentes

| Script | Fuente | Backend | Estado |
|--------|--------|---------|--------|
| `fbref_scraper.py` | FBref.com | `soccerdata` (Chrome headless) | listo |
| (futuro) `statsbomb_loader.py` | StatsBomb Open Data | git/raw GitHub | pendiente |
| (futuro) `transfermarkt_scraper.py` | Transfermarkt | requests + parser | pendiente |
| (futuro) `understat_client.py` | Understat | requests + parser | pendiente |

## Convenciones

- Cada scraper:
  1. Cachea la respuesta cruda (HTML/JSON) en `01_data_raw/_cache/<source>/`.
  2. Parsea a DataFrame.
  3. Guarda parquet en `01_data_raw/<entity>/<source>_<scope>_<stat>_<season>.parquet` vía `lib.io.write_parquet`.
- Cachés son `.gitignored` — se pueden borrar y regenerar.
- Cuando una fuente está detrás de Cloudflare (FBref), usar wrapper con browser real (`soccerdata`). Para fuentes abiertas, `requests` directo está bien.

## FBref — uso

```powershell
# Big 5 Europa, temporada actual, stats estándar
python 06_ingestion\fbref_scraper.py

# Una liga específica + categoría específica + temporada histórica
python 06_ingestion\fbref_scraper.py --comp PL --stat shooting --season 2023-2024

# Todas las categorías de stats para Big 5
python 06_ingestion\fbref_scraper.py --comp Big5 --all-stats

# Forzar re-descarga (ignora caché)
python 06_ingestion\fbref_scraper.py --refresh
```

Códigos de competición: `Big5`, `PL`, `LL`, `SA`, `BL`, `L1`.
Categorías: `standard`, `shooting`, `passing`, `passing_types`, `goal_shot_creation`, `defense`, `possession`, `playing_time`, `misc`, `keeper`, `keeper_adv`.

**Primera ejecución**: ~30–60 s (Chrome cold start + Cloudflare challenge). Subsecuentes: instantáneas desde caché en `01_data_raw/_cache/soccerdata/`.

## Cómo agregar una nueva fuente

1. Crea `06_ingestion/<source>_scraper.py`.
2. Sigue el patrón: caché en `01_data_raw/_cache/<source>/`, output en `01_data_raw/<entity>/`.
3. Importa `lib.io.write_parquet` (no escribas parquet a mano).
4. Documenta el rate limit en una constante al tope del archivo.
5. Crea una skill nueva en `.claude/skills/<source>-ingest/SKILL.md` con los quirks de la fuente.
