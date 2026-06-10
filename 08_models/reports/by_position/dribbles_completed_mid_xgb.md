# Predictor de `dribbles_completed` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.6835**
- RMSE modelo: **0.9465**
- MAE baseline (rolling 5): **0.7332**
- RMSE baseline (rolling 5): **1.1129**
- Mejora MAE vs baseline: **+6.78%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_dribbles_completed | 0.3464 |
| minutes_played | 0.2096 |
| roll_dribbles_completed_10 | 0.1108 |
| roll_minutes_5 | 0.0639 |
| roll_dribbles_completed_5 | 0.0601 |
| days_rest | 0.0449 |
| opp_allows_dribbles_completed_10 | 0.0436 |
| opp_allows_dribbles_completed_5 | 0.0427 |
| roll_dribbles_completed_3 | 0.0419 |
| is_home | 0.0360 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.146 | 0.088 | 216 |
| 1 | 0.314 | 0.306 | 216 |
| 2 | 0.397 | 0.426 | 216 |
| 3 | 0.482 | 0.389 | 216 |
| 4 | 0.576 | 0.532 | 216 |
| 5 | 0.676 | 0.574 | 216 |
| 6 | 0.768 | 0.602 | 216 |
| 7 | 0.897 | 0.657 | 216 |
| 8 | 1.129 | 0.824 | 216 |
| 9 | 1.686 | 1.519 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.