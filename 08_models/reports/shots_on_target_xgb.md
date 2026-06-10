# Predictor de `shots_on_target` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.4046**
- RMSE modelo: **0.5957**
- MAE baseline (rolling 5): **0.3913**
- RMSE baseline (rolling 5): **0.6736**
- Mejora MAE vs baseline: **-3.40%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_shots_on_target | 0.4072 |
| minutes_played | 0.1322 |
| roll_shots_on_target_10 | 0.1179 |
| roll_minutes_5 | 0.0715 |
| roll_shots_on_target_3 | 0.0552 |
| opp_allows_shots_on_target_5 | 0.0536 |
| opp_allows_shots_on_target_10 | 0.0508 |
| roll_shots_on_target_5 | 0.0482 |
| is_home | 0.0368 |
| days_rest | 0.0266 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.091 | 0.071 | 677 |
| 1 | 0.119 | 0.074 | 676 |
| 2 | 0.146 | 0.141 | 676 |
| 3 | 0.175 | 0.173 | 676 |
| 4 | 0.208 | 0.209 | 676 |
| 5 | 0.248 | 0.269 | 676 |
| 6 | 0.293 | 0.300 | 676 |
| 7 | 0.379 | 0.408 | 676 |
| 8 | 0.556 | 0.538 | 676 |
| 9 | 0.948 | 0.861 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.