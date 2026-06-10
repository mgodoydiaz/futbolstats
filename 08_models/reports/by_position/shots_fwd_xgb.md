# Predictor de `shots` — resultados

- Filas de test: **1,652**
- MAE modelo: **1.0639**
- RMSE modelo: **1.4000**
- MAE baseline (rolling 5): **1.2998**
- RMSE baseline (rolling 5): **1.7344**
- Mejora MAE vs baseline: **+18.15%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.4226 |
| career_shots | 0.1492 |
| roll_shots_10 | 0.1167 |
| is_home | 0.0507 |
| roll_shots_5 | 0.0507 |
| opp_allows_shots_10 | 0.0462 |
| roll_shots_3 | 0.0446 |
| opp_allows_shots_5 | 0.0407 |
| roll_minutes_5 | 0.0397 |
| days_rest | 0.0390 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.332 | 0.355 | 166 |
| 1 | 0.587 | 0.600 | 165 |
| 2 | 0.919 | 0.945 | 165 |
| 3 | 1.142 | 1.036 | 165 |
| 4 | 1.336 | 1.491 | 165 |
| 5 | 1.580 | 1.685 | 165 |
| 6 | 1.897 | 1.630 | 165 |
| 7 | 2.238 | 2.248 | 165 |
| 8 | 2.647 | 2.509 | 165 |
| 9 | 3.408 | 3.367 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.