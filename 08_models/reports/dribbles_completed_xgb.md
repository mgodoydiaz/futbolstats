# Predictor de `dribbles_completed` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.6425**
- RMSE modelo: **0.8839**
- MAE baseline (rolling 5): **0.6234**
- RMSE baseline (rolling 5): **0.9956**
- Mejora MAE vs baseline: **-3.06%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_dribbles_completed | 0.4714 |
| roll_dribbles_completed_10 | 0.1686 |
| minutes_played | 0.1114 |
| roll_minutes_5 | 0.0506 |
| roll_dribbles_completed_5 | 0.0464 |
| opp_allows_dribbles_completed_5 | 0.0334 |
| roll_dribbles_completed_3 | 0.0327 |
| opp_allows_dribbles_completed_10 | 0.0314 |
| is_home | 0.0310 |
| days_rest | 0.0230 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.225 | 0.112 | 677 |
| 1 | 0.261 | 0.154 | 676 |
| 2 | 0.313 | 0.200 | 676 |
| 3 | 0.393 | 0.287 | 676 |
| 4 | 0.474 | 0.379 | 676 |
| 5 | 0.556 | 0.450 | 676 |
| 6 | 0.665 | 0.522 | 676 |
| 7 | 0.829 | 0.686 | 676 |
| 8 | 1.072 | 0.982 | 676 |
| 9 | 1.750 | 1.481 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.