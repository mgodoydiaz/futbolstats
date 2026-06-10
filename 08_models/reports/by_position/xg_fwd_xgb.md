# Predictor de `xg` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.2047**
- RMSE modelo: **0.3043**
- MAE baseline (rolling 5): **0.2342**
- RMSE baseline (rolling 5): **0.3580**
- Mejora MAE vs baseline: **+12.60%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2528 |
| career_xg | 0.1762 |
| roll_xg_10 | 0.0917 |
| opp_allows_xg_5 | 0.0779 |
| roll_xg_5 | 0.0722 |
| is_home | 0.0696 |
| roll_minutes_5 | 0.0694 |
| roll_xg_3 | 0.0654 |
| opp_allows_xg_10 | 0.0653 |
| days_rest | 0.0594 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.044 | 0.084 | 166 |
| 1 | 0.080 | 0.088 | 165 |
| 2 | 0.108 | 0.123 | 165 |
| 3 | 0.139 | 0.180 | 165 |
| 4 | 0.169 | 0.181 | 165 |
| 5 | 0.202 | 0.193 | 165 |
| 6 | 0.236 | 0.197 | 165 |
| 7 | 0.281 | 0.286 | 165 |
| 8 | 0.338 | 0.343 | 165 |
| 9 | 0.503 | 0.464 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.