# Remote Control — bitácora de trabajo

Registro de todo lo que hace Claude en modo remoto sobre el proyecto Futbolstats.
Entrada más reciente arriba.

---

## Sesión 2026-06-10 (cont.) — Modelo de goleo y predicciones del Mundial 2026

**Pedido:** modelo de goleo/tarjetas decente que sirva para backtest y Mundial,
con el **método seleccionable por parámetro** en las funciones Python, y
**documentación atractiva** para el usuario.

**Contexto descubierto (dos universos):**
- El **modelo** tiene historial de 7 competiciones StatsBomb (WC 18/22, Euro 20/24,
  Copa América 24, PL 15-16, La Liga 20-21, ISL, Women's WC) — 26,295 jugador-partidos.
- **Pinnacle** cotiza el Mundial 2026 (2,300 cuotas) pero sólo goles y tarjetas.
- Intersección: **239 jugadores** cotizados Y con historial → analizables.
- Backtest con odds reales de player props es inviable (no existe archivo histórico
  de cuotas de goleador); el Mundial sí es real y factible ahora.

### Entregables
| Archivo | Qué hace |
|---------|----------|
| [`lib/scoring.py`](lib/scoring.py) | Estimador de tasa por jugador, **método seleccionable** (rate/per90/shrinkage/xg_shrinkage). Shrinkage Gamma-Poisson hacia media de posición. |
| [`08_models/worldcup_value.py`](08_models/worldcup_value.py) | Value board: cuotas reales Pinnacle vs modelo → EV/Kelly. |
| [`08_models/backtest_scoring.py`](08_models/backtest_scoring.py) | Backtest leak-safe del goleo. **xg_shrinkage gana** (cal-MAE 0.035 vs 0.211 del crudo). |
| [`07_features/build_matches_view.py`](07_features/build_matches_view.py) | +mercados `goals` y `cards` en la vista. |
| [`10_serving/build_dashboard.py`](10_serving/build_dashboard.py) | Dashboard HTML autocontenido del value board. |
| [`10_serving/worldcup/README.md`](10_serving/worldcup/README.md) | Guía del flujo del Mundial. |

### Hallazgos
1. **xg_shrinkage es el mejor método** (validado por calibración leak-safe). Es el
   default del value board.
2. El value alto suele venir de **defensores con poca muestra** (creerle a Pinnacle,
   no al modelo). Los picks creíbles son de muestra grande (Modrić 23 PJ, Mané 40 PJ).
   El filtro `--min-matches` los separa.

### Pendientes
- Wiring de odds reales → recálculo de `match_value` (hoy el value board del Mundial
  es un flujo aparte; la vista usa odds sintéticas).
- Modelo de minutos esperados (hoy se usa el promedio histórico del jugador).
- Ajuste por rival para selecciones (ClubElo es de clubes, no mapea directo).

---

## Sesión 2026-06-10 — Pipeline de value betting (player props)

**Pedido del usuario:** revisar el proyecto, crear documentación para usar Jupyter
con los partidos, reordenar la base de datos, y construir código que analice las
cuotas de las casas de apuestas y calcule el threshold para decidir si conviene
apostar. Trabajo en remoto vía `/remote-control`.

**Decisiones acordadas (vía preguntas):**
- Mercado: **player props** (over/under de stats individuales).
- Fuente de cuotas: **scrapear Pinnacle**.
- Formato: **notebook + módulos Python reutilizables** en paralelo.
- Objetivo: **backtest primero, live después** con la misma lógica.
- Threshold: **lo define el usuario** en el notebook; el código expone EV, Kelly,
  prob_implícita y prob_model como columnas.

### Git
- `git init -b main`, remoto → https://github.com/mgodoydiaz/futbolstats (público).
- `.gitattributes` para normalizar line endings (parquet/csv/ipynb como binarios).
- Gitignore ampliado: eventos StatsBomb crudos (~206 MB, regenerables), odds
  sintéticas (`match_odds`/`match_value`), snapshots de Pinnacle (`01_data_raw/odds/`).
- 4 commits, todos pusheados (salvo el del paso 4, sin push por instrucción explícita).

### Entregables

| Paso | Archivo(s) | Qué hace |
|------|-----------|----------|
| 1 | [`lib/betting.py`](lib/betting.py), [`tests/test_betting.py`](tests/test_betting.py) | Matemática pura: conversión de odds, remove-vig (proporcional/power), Poisson/NegBinomial over-under, EV, Kelly fraccional. **33 tests verdes.** |
| 2 | [`07_features/build_matches_view.py`](07_features/build_matches_view.py) | Reorganiza la player-match table en una vista centrada en partidos: `fixtures`, `match_players` (predicción λ leak-safe), `match_odds`, `match_value` (EV/Kelly + resultado). Odds sintéticas position-aware. Vectorizado con scipy. |
| 3 | [`09_correlations/notebooks/01_match_betting.ipynb`](09_correlations/notebooks/01_match_betting.ipynb) | Notebook end-to-end: EV/Kelly/prob por columnas (sin threshold hard-coded), calibración, backtest de ROI. Generado por `_gen_notebook.py`. |
| 4 | [`06_ingestion/pinnacle_scraper.py`](06_ingestion/pinnacle_scraper.py) | Cliente de la API guest JSON de Pinnacle (Arcadia). Sin Selenium ni Cloudflare. |
| 5 | [`lib/backtest.py`](lib/backtest.py), [`08_models/backtest_betting.py`](08_models/backtest_betting.py), docs | Backtest reusable + reporte markdown. README del notebook y sección de tesis LaTeX. |

### Resultados verificados
- Vista construida: **908 fixtures, 26,295 match-players, 788k apuestas cotizadas**.
- Notebook corre las 18 celdas end-to-end.
- Scraper Pinnacle en vivo: **2,300 cuotas reales, 1,283 mapeadas a player_id**.
- Backtest: **calibración MAE 0.025**; median EV ≈ −vig (señal sana de mercado real).

### Hallazgos importantes
1. **Pinnacle para fútbol sólo cotiza props de goles y tarjetas** (anytime/first
   goalscorer, to score, to be booked). NO ofrece over/under de tiros/tackles/pases
   (eso es Bet365). Validado contra la API real.
2. **Las odds del backtest son sintéticas** (mercado blando cotizado por posición).
   El ROI positivo valida la *lógica*, no es edge real.

### Pendientes (follow-up documentado)
- Columnas `lam_goals` / `lam_cards` en `match_players` (para usar odds de Pinnacle).
- Wiring de `01_data_raw/odds/` → schema `match_odds` → recálculo de `match_value`.
- Enchufar predicciones XGBoost (re-entrenadas con `count:poisson`) en vez del baseline.
- Validar calibración out-of-sample (el reporte actual es in-sample).

---
