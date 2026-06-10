# 🏆 Predicciones Mundial 2026 — value board

Análisis de valor sobre cuotas reales de **Pinnacle** para los dos mercados de
player props que la casa cotiza en fútbol: **goleador** (anytime goalscorer) y
**a ser amonestado** (to be booked).

## Cómo generarlo (3 comandos)

```powershell
conda activate futbolstats

# 1. cuotas reales de Pinnacle (snapshot del día)
python 06_ingestion\pinnacle_scraper.py

# 2. cruzar con el modelo → value board (markdown + parquet)
python 08_models\worldcup_value.py --min-matches 8

# 3. dashboard HTML lindo (se abre en el navegador)
python 10_serving\build_dashboard.py
#    -> 10_serving\worldcup\dashboard.html
```

## El pipeline

```
Pinnacle (odds reales)  ─┐
                         ├─►  worldcup_value.py  ─►  value_board.parquet ─► dashboard.html
historial StatsBomb ──► lib.scoring (xg_shrinkage)
```

1. **`pinnacle_scraper.py`** baja las cuotas reales (sólo goles y tarjetas — es lo
   único que Pinnacle cotiza en fútbol).
2. **`lib.scoring`** estima la tasa de goles/tarjetas de cada jugador con
   encogimiento (shrinkage) para no creerle a rachas de pocos partidos.
3. **`worldcup_value.py`** calcula `EV = p_model × cuota − 1` y el stake Kelly.
4. **`build_dashboard.py`** lo renderiza en HTML.

## Cómo leer la tabla

| Columna | Qué es |
|---------|--------|
| **p modelo** | P(el jugador marca / es amonestado) según el modelo |
| **cuota** | cuota decimal de Pinnacle |
| **p impl.** | `1/cuota` — probabilidad implícita (incluye el margen de la casa) |
| **EV** | valor esperado por unidad. **EV > 0 ⇒ el modelo ve el evento más probable que la cuota** |
| **Kelly** | fracción del bankroll sugerida (quarter-Kelly). 0 = no apostar |
| **⚠ / PJ** | partidos de historial. Menos de 8 = muestra chica, desconfiá |

## Por qué confiar (y por qué no)

**A favor:** el modelo `xg_shrinkage` fue validado leak-safe en histórico
([`08_models/reports/scoring_backtest.md`](../../08_models/reports/scoring_backtest.md)):
calibración casi perfecta (cal-MAE **0.035**, LogLoss **0.27** vs 0.56 del baseline
crudo). Cuando dice 25 %, acierta ~25 %.

**En contra:** Pinnacle es un book *sharp* (afina mucho). El modelo es más crudo,
sobre todo en jugadores con poca muestra (defensores que marcaron 1 gol suelto).
Los EV gigantes (>50 %) casi siempre son esos casos — el filtro `--min-matches 8`
los saca. Los picks creíbles son los de muestra grande (ej. Modrić 23 PJ, Mané 40 PJ).

> ⚠️ **Esto es análisis estadístico, no asesoría de apuestas.** Apostar dinero
> conlleva riesgo de pérdida total. Un EV positivo en el modelo no garantiza ganancia.

## Ajustes

```powershell
# método del modelo (rate | per90 | shrinkage | xg_shrinkage)
python 08_models\worldcup_value.py --goal-method xg_shrinkage --card-method shrinkage

# más estricto con la muestra y el encogimiento
python 08_models\worldcup_value.py --min-matches 10 --prior-strength 6

# sólo apuestas con EV positivo, top 50 en el reporte
python 08_models\worldcup_value.py --ev-min 0.0 --top 50
```

## Limitación de cobertura

Sólo se valúan jugadores **cotizados por Pinnacle Y con historial en nuestros datos
StatsBomb** (≈ 240). Selecciones/jugadores sin historial (debutantes, ligas no
cubiertas) no se pueden predecir. Para ampliar cobertura: cargar más competiciones
con `statsbomb_loader.py`.
