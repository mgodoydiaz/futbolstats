# Predictor de `shots` — resultados

- Filas de test: **473**
- MAE modelo: **0.0100**
- RMSE modelo: **0.0794**
- MAE baseline (rolling 5): **0.0072**
- RMSE baseline (rolling 5): **0.0807**
- Mejora MAE vs baseline: **-39.24%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_shots_3 | 0.0000 |
| roll_shots_5 | 0.0000 |
| roll_shots_10 | 0.0000 |
| career_shots | 0.0000 |
| days_rest | 0.0000 |
| roll_minutes_5 | 0.0000 |
| is_home | 0.0000 |
| minutes_played | 0.0000 |
| opp_allows_shots_5 | 0.0000 |
| opp_allows_shots_10 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.004 | 0.000 | 48 |
| 1 | 0.004 | 0.000 | 47 |
| 2 | 0.004 | 0.000 | 47 |
| 3 | 0.004 | 0.000 | 47 |
| 4 | 0.004 | 0.021 | 48 |
| 5 | 0.004 | 0.000 | 47 |
| 6 | 0.004 | 0.000 | 47 |
| 7 | 0.004 | 0.043 | 47 |
| 8 | 0.004 | 0.000 | 47 |
| 9 | 0.004 | 0.000 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.