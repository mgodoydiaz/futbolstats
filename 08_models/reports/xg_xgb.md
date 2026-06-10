# Predictor de `xg` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.1191**
- RMSE modelo: **0.2126**
- MAE baseline (rolling 5): **0.1258**
- RMSE baseline (rolling 5): **0.2395**
- Mejora MAE vs baseline: **+5.31%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_xg | 0.3538 |
| roll_xg_10 | 0.1757 |
| minutes_played | 0.1129 |
| opp_allows_xg_10 | 0.0621 |
| roll_minutes_5 | 0.0584 |
| opp_allows_xg_5 | 0.0538 |
| days_rest | 0.0481 |
| roll_xg_3 | 0.0475 |
| roll_xg_5 | 0.0471 |
| is_home | 0.0406 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.017 | 0.021 | 677 |
| 1 | 0.027 | 0.030 | 676 |
| 2 | 0.039 | 0.041 | 676 |
| 3 | 0.051 | 0.059 | 676 |
| 4 | 0.063 | 0.073 | 676 |
| 5 | 0.078 | 0.091 | 676 |
| 6 | 0.098 | 0.105 | 676 |
| 7 | 0.134 | 0.123 | 676 |
| 8 | 0.192 | 0.191 | 676 |
| 9 | 0.344 | 0.323 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.