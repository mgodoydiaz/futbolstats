# Backtest leak-safe — modelo de goleo (P de marcar)


17,052 jugador-partidos evaluados (≥3 partidos de historial previo). Tasa base de gol: **0.096**.


## Comparación de métodos

Menor Brier / LogLoss = mejor. `cal_mae` = error medio de calibración.

| método | Brier | LogLoss | cal_MAE |
| --- | --- | --- | --- |
| rate | 0.0860 | 0.5571 | 0.2111 |
| shrinkage | 0.0801 | 0.2833 | 0.1589 |
| xg_shrinkage | 0.0782 | 0.2719 | 0.0352 |

**Mejor método: `xg_shrinkage`** (menor LogLoss).


## Calibración del mejor método (`xg_shrinkage`)

`gap = obs − pred`; cercano a 0 ⇒ probabilidades fiables.

| bin p | n | pred | obs | gap |
| --- | --- | --- | --- | --- |
| (-0.001, 0.1] | 11687 | 0.041 | 0.044 | +0.003 |
| (0.1, 0.2] | 3010 | 0.144 | 0.145 | +0.001 |
| (0.2, 0.3] | 1532 | 0.243 | 0.265 | +0.022 |
| (0.3, 0.4] | 607 | 0.344 | 0.316 | -0.028 |
| (0.4, 0.5] | 194 | 0.436 | 0.428 | -0.008 |
| (0.5, 0.6] | 20 | 0.544 | 0.600 | +0.056 |
| (0.6, 0.7] | 2 | 0.628 | 0.500 | -0.128 |

## Lectura

- El **shrinkage** debería ganarle al **rate** crudo: el rate sobreestima a jugadores con racha en pocos partidos (Brier/LogLoss peor).
- **xg_shrinkage** suele calibrar mejor en la cola alta: xG es menos ruidoso que goles para estimar la tasa real.
- Si la calibración del mejor método es buena, el EV del value board del Mundial es confiable *para jugadores con muestra* (ojo con `prior_matches` bajo).
