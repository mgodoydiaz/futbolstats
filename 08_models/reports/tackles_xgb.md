# Predictor de `tackles` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.9367**
- RMSE modelo: **1.2718**
- MAE baseline (rolling 5): **1.0496**
- RMSE baseline (rolling 5): **1.4902**
- Mejora MAE vs baseline: **+10.75%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_tackles | 0.4922 |
| roll_tackles_10 | 0.1311 |
| minutes_played | 0.1260 |
| roll_tackles_5 | 0.0691 |
| roll_tackles_3 | 0.0442 |
| roll_minutes_5 | 0.0388 |
| opp_allows_tackles_10 | 0.0377 |
| opp_allows_tackles_5 | 0.0310 |
| is_home | 0.0167 |
| days_rest | 0.0133 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.262 | 0.158 | 677 |
| 1 | 0.392 | 0.308 | 676 |
| 2 | 0.615 | 0.595 | 676 |
| 3 | 0.850 | 0.808 | 676 |
| 4 | 1.097 | 1.129 | 676 |
| 5 | 1.266 | 1.246 | 676 |
| 6 | 1.447 | 1.546 | 676 |
| 7 | 1.669 | 1.723 | 676 |
| 8 | 1.988 | 1.984 | 676 |
| 9 | 2.702 | 2.574 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.