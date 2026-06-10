# Predictor de `passes_completed` — resultados

- Filas de test: **2,154**
- MAE modelo: **12.6772**
- RMSE modelo: **17.1541**
- MAE baseline (rolling 5): **17.2196**
- RMSE baseline (rolling 5): **22.6830**
- Mejora MAE vs baseline: **+26.38%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_passes_completed | 0.3196 |
| roll_passes_completed_10 | 0.2648 |
| minutes_played | 0.1100 |
| roll_passes_completed_5 | 0.1044 |
| opp_allows_passes_completed_10 | 0.0571 |
| opp_allows_passes_completed_5 | 0.0466 |
| roll_minutes_5 | 0.0324 |
| is_home | 0.0260 |
| roll_passes_completed_3 | 0.0218 |
| days_rest | 0.0174 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 8.714 | 6.838 | 216 |
| 1 | 20.436 | 18.233 | 215 |
| 2 | 26.957 | 25.949 | 215 |
| 3 | 31.521 | 33.292 | 216 |
| 4 | 35.735 | 35.972 | 215 |
| 5 | 40.354 | 41.902 | 215 |
| 6 | 44.458 | 45.648 | 216 |
| 7 | 49.283 | 48.316 | 215 |
| 8 | 55.920 | 54.958 | 215 |
| 9 | 71.506 | 69.454 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.