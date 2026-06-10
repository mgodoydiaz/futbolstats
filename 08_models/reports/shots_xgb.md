# Predictor de `shots` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.7776**
- RMSE modelo: **1.0806**
- MAE baseline (rolling 5): **0.8418**
- RMSE baseline (rolling 5): **1.2505**
- Mejora MAE vs baseline: **+7.62%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_shots | 0.4760 |
| minutes_played | 0.1256 |
| roll_shots_10 | 0.1183 |
| roll_shots_5 | 0.0760 |
| roll_minutes_5 | 0.0473 |
| is_home | 0.0428 |
| opp_allows_shots_10 | 0.0375 |
| opp_allows_shots_5 | 0.0317 |
| roll_shots_3 | 0.0269 |
| days_rest | 0.0178 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.181 | 0.182 | 677 |
| 1 | 0.270 | 0.263 | 676 |
| 2 | 0.389 | 0.404 | 676 |
| 3 | 0.524 | 0.549 | 676 |
| 4 | 0.642 | 0.601 | 676 |
| 5 | 0.780 | 0.817 | 676 |
| 6 | 0.944 | 0.883 | 676 |
| 7 | 1.192 | 1.163 | 676 |
| 8 | 1.633 | 1.571 | 676 |
| 9 | 2.622 | 2.453 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.