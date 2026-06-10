# Predictor de `shots_on_target` — resultados

- Filas de test: **473**
- MAE modelo: **0.0021**
- RMSE modelo: **0.0460**
- MAE baseline (rolling 5): **0.0021**
- RMSE baseline (rolling 5): **0.0460**
- Mejora MAE vs baseline: **+0.00%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_shots_on_target_3 | 0.0000 |
| roll_shots_on_target_5 | 0.0000 |
| roll_shots_on_target_10 | 0.0000 |
| career_shots_on_target | 0.0000 |
| days_rest | 0.0000 |
| roll_minutes_5 | 0.0000 |
| is_home | 0.0000 |
| minutes_played | 0.0000 |
| opp_allows_shots_on_target_5 | 0.0000 |
| opp_allows_shots_on_target_10 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.000 | 0.000 | 48 |
| 1 | 0.000 | 0.000 | 47 |
| 2 | 0.000 | 0.000 | 47 |
| 3 | 0.000 | 0.000 | 47 |
| 4 | 0.000 | 0.000 | 48 |
| 5 | 0.000 | 0.000 | 47 |
| 6 | 0.000 | 0.000 | 47 |
| 7 | 0.000 | 0.021 | 47 |
| 8 | 0.000 | 0.000 | 47 |
| 9 | 0.000 | 0.000 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.