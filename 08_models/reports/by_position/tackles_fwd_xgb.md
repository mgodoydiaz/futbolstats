# Predictor de `tackles` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.7469**
- RMSE modelo: **0.9780**
- MAE baseline (rolling 5): **0.7927**
- RMSE baseline (rolling 5): **1.1303**
- Mejora MAE vs baseline: **+5.78%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2215 |
| roll_tackles_10 | 0.2133 |
| career_tackles | 0.1623 |
| roll_tackles_3 | 0.0843 |
| roll_tackles_5 | 0.0698 |
| roll_minutes_5 | 0.0680 |
| opp_allows_tackles_5 | 0.0569 |
| days_rest | 0.0500 |
| opp_allows_tackles_10 | 0.0451 |
| is_home | 0.0288 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.257 | 0.157 | 166 |
| 1 | 0.389 | 0.224 | 165 |
| 2 | 0.515 | 0.285 | 165 |
| 3 | 0.624 | 0.624 | 165 |
| 4 | 0.698 | 0.691 | 165 |
| 5 | 0.756 | 0.727 | 165 |
| 6 | 0.846 | 0.830 | 165 |
| 7 | 1.038 | 1.018 | 165 |
| 8 | 1.226 | 1.333 | 165 |
| 9 | 1.552 | 1.566 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.