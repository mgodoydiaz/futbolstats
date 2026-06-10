# Predictor de `fouls_drawn` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.8665**
- RMSE modelo: **1.1277**
- MAE baseline (rolling 5): **0.9899**
- RMSE baseline (rolling 5): **1.3478**
- Mejora MAE vs baseline: **+12.47%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2860 |
| career_fouls_drawn | 0.1863 |
| roll_fouls_drawn_10 | 0.1148 |
| roll_fouls_drawn_5 | 0.0809 |
| roll_fouls_drawn_3 | 0.0709 |
| roll_minutes_5 | 0.0678 |
| opp_allows_fouls_drawn_10 | 0.0562 |
| is_home | 0.0499 |
| days_rest | 0.0446 |
| opp_allows_fouls_drawn_5 | 0.0425 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.314 | 0.193 | 166 |
| 1 | 0.492 | 0.436 | 165 |
| 2 | 0.675 | 0.582 | 165 |
| 3 | 0.827 | 0.721 | 165 |
| 4 | 0.988 | 0.842 | 165 |
| 5 | 1.165 | 1.145 | 165 |
| 6 | 1.280 | 1.442 | 165 |
| 7 | 1.427 | 1.412 | 165 |
| 8 | 1.648 | 1.691 | 165 |
| 9 | 2.219 | 2.114 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.