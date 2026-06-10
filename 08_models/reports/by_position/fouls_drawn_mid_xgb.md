# Predictor de `fouls_drawn` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.8588**
- RMSE modelo: **1.1467**
- MAE baseline (rolling 5): **0.9863**
- RMSE baseline (rolling 5): **1.3510**
- Mejora MAE vs baseline: **+12.93%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2618 |
| career_fouls_drawn | 0.2331 |
| roll_fouls_drawn_5 | 0.1106 |
| roll_fouls_drawn_10 | 0.0719 |
| roll_fouls_drawn_3 | 0.0622 |
| is_home | 0.0592 |
| roll_minutes_5 | 0.0541 |
| opp_allows_fouls_drawn_5 | 0.0540 |
| days_rest | 0.0481 |
| opp_allows_fouls_drawn_10 | 0.0450 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.264 | 0.199 | 216 |
| 1 | 0.464 | 0.426 | 216 |
| 2 | 0.630 | 0.634 | 216 |
| 3 | 0.795 | 0.824 | 216 |
| 4 | 0.929 | 0.940 | 216 |
| 5 | 1.046 | 1.250 | 216 |
| 6 | 1.229 | 1.181 | 216 |
| 7 | 1.409 | 1.148 | 216 |
| 8 | 1.616 | 1.667 | 216 |
| 9 | 2.163 | 2.319 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.