# Predictor de `fouls_committed` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.7877**
- RMSE modelo: **1.0209**
- MAE baseline (rolling 5): **0.8638**
- RMSE baseline (rolling 5): **1.1885**
- Mejora MAE vs baseline: **+8.82%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_fouls_committed | 0.3477 |
| minutes_played | 0.1768 |
| roll_fouls_committed_10 | 0.1497 |
| roll_minutes_5 | 0.0845 |
| roll_fouls_committed_5 | 0.0537 |
| opp_allows_fouls_committed_10 | 0.0469 |
| roll_fouls_committed_3 | 0.0457 |
| is_home | 0.0356 |
| opp_allows_fouls_committed_5 | 0.0337 |
| days_rest | 0.0257 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.262 | 0.219 | 677 |
| 1 | 0.376 | 0.322 | 676 |
| 2 | 0.568 | 0.510 | 676 |
| 3 | 0.760 | 0.731 | 676 |
| 4 | 0.897 | 0.822 | 676 |
| 5 | 1.020 | 0.993 | 676 |
| 6 | 1.127 | 1.083 | 676 |
| 7 | 1.247 | 1.200 | 676 |
| 8 | 1.404 | 1.377 | 676 |
| 9 | 1.706 | 1.678 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.