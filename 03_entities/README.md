# 03_entities — Catálogos maestros

Cada CSV es la **fuente de verdad** para los IDs canónicos del proyecto. Se almacenan como CSV (no parquet) porque son chicos y a veces se editan a mano.

| Archivo | Filas (seed) | Llave primaria | Descripción |
|---------|--------------|----------------|-------------|
| `countries.csv` | 62 | `country_id` (ISO alpha-3) | Países FIFA + confederación |
| `competitions.csv` | 21 | `competition_id` | Ligas y torneos rastreados |
| `players.csv` | 0 | `player_id` | Se puebla desde scrapers |
| `teams.csv` | 0 | `team_id` | Se puebla desde scrapers |

## Convenciones de ID

- **Country**: ISO 3166-1 alpha-3 (`ARG`, `BRA`, `ESP`). Usa `INT` para competiciones internacionales.
- **Player / Team / Competition**: prefijo de fuente + ID nativo de la fuente: `fbref_d70ce98e`, `sb_11195`.

Nunca uses el ID nativo pelado — siempre con prefijo. Esto permite cruzar registros entre fuentes cuando agreguemos StatsBomb, Transfermarkt, etc.

## Lectura desde Python

```python
from lib.io import read_entities
countries = read_entities("countries")
competitions = read_entities("competitions")
```

## Schema

Definido en [`lib/schemas.py`](../lib/schemas.py) → `PLAYERS`, `TEAMS`, `COUNTRIES`, `COMPETITIONS`.
