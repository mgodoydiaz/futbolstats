# Predictor de `shots_on_target` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.4201**
- RMSE modelo: **0.5806**
- MAE baseline (rolling 5): **0.4089**
- RMSE baseline (rolling 5): **0.6740**
- Mejora MAE vs baseline: **-2.74%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_shots_on_target | 0.3032 |
| roll_shots_on_target_10 | 0.1688 |
| minutes_played | 0.1415 |
| roll_shots_on_target_5 | 0.0762 |
| is_home | 0.0628 |
| roll_shots_on_target_3 | 0.0621 |
| roll_minutes_5 | 0.0548 |
| opp_allows_shots_on_target_10 | 0.0471 |
| days_rest | 0.0458 |
| opp_allows_shots_on_target_5 | 0.0379 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.107 | 0.083 | 216 |
| 1 | 0.161 | 0.185 | 216 |
| 2 | 0.186 | 0.213 | 216 |
| 3 | 0.221 | 0.222 | 216 |
| 4 | 0.246 | 0.231 | 216 |
| 5 | 0.269 | 0.250 | 216 |
| 6 | 0.299 | 0.319 | 216 |
| 7 | 0.351 | 0.440 | 216 |
| 8 | 0.443 | 0.532 | 216 |
| 9 | 0.663 | 0.625 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.