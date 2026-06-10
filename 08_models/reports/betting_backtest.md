# Backtest — pipeline de value betting
Generado desde `match_value.parquet` (788,850 apuestas cotizadas, bookmaker=`synthetic`).
> ⚠️ **Odds sintéticas** (mercado blando cotizado por posición). Los ROI de
> abajo miden que la *lógica* del pipeline funciona, NO un edge real. Contra un
> book sharp como Pinnacle el ROI esperado es ≈ −vig. Apostar arriesga el capital.

## 1 · Barrido de threshold de EV
ROI = profit / total apostado. `flat` = 1 unidad por apuesta; `kelly` = fracción quarter-Kelly del bankroll.
| ev_min | stake | n_bets | staked | profit | roi | hit_rate | mean_ev |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0000 | flat | 332817 | 332817.0000 | 47444.6300 | 0.1426 | 0.5924 | 0.5927 |
| 0.0000 | kelly | 332817 | 33365.6289 | 5963.4491 | 0.1787 | 0.5924 | 0.5927 |
| 0.0200 | flat | 309465 | 309465.0000 | 47229.0770 | 0.1526 | 0.5846 | 0.6366 |
| 0.0200 | kelly | 309465 | 32268.3064 | 5969.2086 | 0.1850 | 0.5846 | 0.6366 |
| 0.0500 | flat | 286555 | 286555.0000 | 46736.9190 | 0.1631 | 0.5729 | 0.6848 |
| 0.0500 | kelly | 286555 | 30985.5300 | 5949.2323 | 0.1920 | 0.5729 | 0.6848 |
| 0.1000 | flat | 240288 | 240288.0000 | 45070.8300 | 0.1876 | 0.5472 | 0.8026 |
| 0.1000 | kelly | 240288 | 26303.7005 | 5766.2340 | 0.2192 | 0.5472 | 0.8026 |
| 0.2000 | flat | 176639 | 176639.0000 | 41307.5030 | 0.2339 | 0.5076 | 1.0400 |
| 0.2000 | kelly | 176639 | 20235.9582 | 5391.2956 | 0.2664 | 0.5076 | 1.0400 |
| 0.4000 | flat | 102465 | 102465.0000 | 31850.3900 | 0.3108 | 0.4277 | 1.5845 |
| 0.4000 | kelly | 102465 | 11311.3213 | 4228.5861 | 0.3738 | 0.4277 | 1.5845 |

## 2 · Calibración (predicho vs observado)
`gap = obs − pred`. Cercano a 0 en todos los bins ⇒ probabilidades bien calibradas (precondición para confiar en el EV).
| bin | n | pred | obs | gap |
| --- | --- | --- | --- | --- |
| (-0.001, 0.1] | 124563 | 0.0181 | 0.1058 | 0.0877 |
| (0.1, 0.2] | 62037 | 0.1563 | 0.1803 | 0.0241 |
| (0.2, 0.3] | 65177 | 0.2497 | 0.2387 | -0.0111 |
| (0.3, 0.4] | 66175 | 0.3511 | 0.3496 | -0.0015 |
| (0.4, 0.5] | 76473 | 0.4533 | 0.4522 | -0.0011 |
| (0.5, 0.6] | 76473 | 0.5467 | 0.5478 | 0.0011 |
| (0.6, 0.7] | 66175 | 0.6489 | 0.6504 | 0.0015 |
| (0.7, 0.8] | 65177 | 0.7503 | 0.7613 | 0.0111 |
| (0.8, 0.9] | 62037 | 0.8437 | 0.8197 | -0.0241 |
| (0.9, 1.0] | 124563 | 0.9819 | 0.8942 | -0.0877 |

MAE de calibración: **0.0251**

## 3 · Curva de bankroll (quarter-Kelly, orden cronológico)
Threshold EV > 0.05. Bankroll base 1.0, aditivo.
- apuestas: **286,555**
- hit rate: **0.573**
- ROI (flat): **+0.1631**
- bankroll final: **5950.232**
- max drawdown: **-38.002**

## Lectura
- El **median EV** del universo completo ≈ −vig es la señal sana: la mayoría de
  cuotas son −EV, como en cualquier mercado.
- Donde el ROI realizado **sigue** al EV esperado al subir el threshold, la lógica
  de selección está rankeando bien.
- La **calibración** es la guardarraíl: si los bins altos de `p_model` aciertan
  menos de lo que predicen (overconfidence), el EV de favoritos está inflado.
- Antes de jugar plata real: re-entrenar los targets sparse con `count:poisson`
  y validar calibración out-of-sample, no in-sample.
