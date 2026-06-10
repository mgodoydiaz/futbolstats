# Predictor de `shots` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.5880**
- RMSE modelo: **0.7480**
- MAE baseline (rolling 5): **0.6026**
- RMSE baseline (rolling 5): **0.8787**
- Mejora MAE vs baseline: **+2.41%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_shots | 0.2554 |
| roll_shots_10 | 0.1644 |
| minutes_played | 0.1301 |
| roll_shots_5 | 0.1092 |
| roll_shots_3 | 0.0770 |
| opp_allows_shots_5 | 0.0611 |
| opp_allows_shots_10 | 0.0556 |
| is_home | 0.0545 |
| roll_minutes_5 | 0.0511 |
| days_rest | 0.0415 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.197 | 0.157 | 216 |
| 1 | 0.314 | 0.312 | 215 |
| 2 | 0.387 | 0.335 | 215 |
| 3 | 0.410 | 0.431 | 216 |
| 4 | 0.435 | 0.400 | 215 |
| 5 | 0.485 | 0.572 | 215 |
| 6 | 0.568 | 0.514 | 216 |
| 7 | 0.623 | 0.572 | 215 |
| 8 | 0.691 | 0.665 | 215 |
| 9 | 0.872 | 0.699 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.