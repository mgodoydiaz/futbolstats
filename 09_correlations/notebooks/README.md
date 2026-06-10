# Notebooks — análisis de partidos y apuestas

Guía para usar Jupyter con los partidos: cargar la vista, analizar cuotas y
decidir el threshold de apuesta. Pensado para que lo corras de cero.

## TL;DR

```powershell
conda activate futbolstats

# 1. (una vez) construir la vista de partidos con odds sintéticas
python 07_features\build_matches_view.py --source statsbomb --synthetic

# 2. abrir el notebook
jupyter lab 09_correlations\notebooks\01_match_betting.ipynb
```

Corré las celdas de arriba a abajo. Si `match_value.parquet` no existe, la celda 2
lo genera sola.

## Qué hace el pipeline

```
player-match table ──► build_matches_view.py ──► matches_view/ ──► notebook
   (stats por jugador)        (predicción λ + EV)     (4 parquets)    (decisión)
```

El flujo convierte **predicción del modelo → probabilidad → EV vs cuota → Kelly**.
No decide por vos: expone las métricas como columnas y vos elegís el umbral.

## La vista de partidos (`02_data_processed/matches_view/`)

| Archivo | Una fila por | Contenido | Versionado |
|---------|--------------|-----------|:----------:|
| `fixtures.parquet` | partido | fecha, liga, season, local/visitante, `status` (past/upcoming) | ✅ |
| `match_players.parquet` | (partido, jugador) | predicción `lam_<market>` leak-safe + `actual_<market>` | ✅ |
| `match_odds.parquet` | (partido, jugador, market, line, side) | cuota, bookmaker, timestamp | ❌ regenerable |
| `match_value.parquet` | (partido, jugador, market, line, side) | `p_model`, `implied_prob`, `edge`, `ev`, `kelly`, `won` | ❌ regenerable |

`match_value` es **la tabla que usa el notebook**. Columnas clave:

- `p_model` — probabilidad del modelo de que el over/under acierte.
- `implied_prob` — probabilidad implícita en la cuota (incluye el vig).
- `edge` — `p_model − implied_prob` (señal rápida).
- `ev` — valor esperado por unidad apostada. **`ev > 0` ⇒ apuesta +EV.**
- `kelly_full`, `kelly_25pct` — fracción del bankroll a apostar (quarter-Kelly recomendado).
- `won` — resultado realizado (1 ganó, 0 perdió, `NaN` push o aún no jugado). Para
  backtest.

## Cómo se calcula (módulos en `lib/`)

- **`lib.betting`** — matemática pura: conversión de odds, remove-vig, distribuciones
  de conteo over/under (Poisson / Negative-Binomial), EV y Kelly. Tiene tests en
  `tests/test_betting.py` (`python -m pytest tests/test_betting.py -q`).
- **`lib.features`** — la predicción `lam_<market>` es el baseline **leak-safe**
  (rolling-5 → career → media poblacional, todo `shift(1)`). Para usar predicciones
  de XGBoost, sobre-escribí las columnas `lam_<market>` de `match_players.parquet`.
- **`lib.backtest`** — barrido de threshold, calibración y curva de bankroll.

## El threshold lo definís vos

En la **sección 3** del notebook:

```python
EV_MIN    = 0.05   # apuesta sólo si el edge esperado supera 5%
KELLY_MIN = 0.01   # y el stake quarter-Kelly supera 1% del bankroll
```

No hay umbral hard-coded. Subir `EV_MIN` deja menos apuestas pero de más calidad.
La **sección 5** muestra el trade-off: cómo cambia el ROI según el threshold.

## La calibración es el guardarraíl

La **sección 4** grafica `p_model` vs frecuencia real de acierto. Si la curva se
aleja de la diagonal, las probabilidades mienten y el EV no sirve. En la vista
sintética el modelo está bien calibrado en el centro pero **sobre-confiado en
favoritos extremos** (predice 0.98, acierta 0.89) — ojo con apostar overs muy
cargados. Reporte completo: `08_models/reports/betting_backtest.md` (regenerable
con `python 08_models\backtest_betting.py`).

## Modo backtest vs modo live

**Backtest (default)** — odds sintéticas + outcomes realizados. Sirve para validar
que la *lógica* funciona. ⚠️ El ROI positivo del backtest sintético **no es edge
real**: el mercado sintético es blando. Contra un book sharp el EV esperado es ≈ −vig.

**Live** — reemplazás las odds sintéticas por cuotas reales de Pinnacle:

```powershell
# 1. scrapear cuotas reales (sólo goles y tarjetas en fútbol — ver nota abajo)
python 06_ingestion\pinnacle_scraper.py --league "Premier League"

# 2. reconstruir la vista usando esas odds (en vez de --synthetic)
#    (pendiente: wiring de 01_data_raw/odds/ -> match_odds; ver "Limitaciones")
python 07_features\build_matches_view.py --source statsbomb
```

Para partidos futuros `won` es `NaN` (no se jugaron): filtrá sólo por `ev`/`kelly`.

## Limitaciones conocidas (lo que falta)

1. **Pinnacle fútbol = sólo goles y tarjetas.** No cotiza over/under de tiros/tackles/
   pases (eso es Bet365). Los mercados `shots`/`tackles` de la vista sólo se llenan
   contra un book que los ofrezca. Contra Pinnacle, el value corre sobre
   `anytime_goalscorer` y `to_be_booked`, que necesitan columnas `lam_goals` /
   `lam_cards` (todavía no en `match_players` — son el siguiente paso).
2. **Wiring odds reales → `match_odds`.** El scraper escribe a `01_data_raw/odds/`;
   falta el paso que mapea esas filas al schema `match_odds` y re-calcula `match_value`.
3. **Predicción = baseline rolling.** Para edge real conviene enchufar los XGBoost
   de `08_models/` (re-entrenados con `count:poisson` para los targets sparse).
4. **Calibración out-of-sample.** El reporte actual es in-sample. Antes de jugar
   plata, validar calibración en un hold-out temporal.

## Aviso

Esto es análisis estadístico personal, **no** asesoría de apuestas. Apostar dinero
conlleva riesgo de pérdida total. El edge en un backtest no garantiza edge futuro.
