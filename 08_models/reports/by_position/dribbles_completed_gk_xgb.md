# Predictor de `dribbles_completed` — resultados

- Filas de test: **473**
- MAE modelo: **0.0331**
- RMSE modelo: **0.1208**
- MAE baseline (rolling 5): **0.0351**
- RMSE baseline (rolling 5): **0.1529**
- Mejora MAE vs baseline: **+5.67%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_minutes_5 | 0.2746 |
| days_rest | 0.2715 |
| minutes_played | 0.2038 |
| career_dribbles_completed | 0.1363 |
| is_home | 0.1139 |
| roll_dribbles_completed_3 | 0.0000 |
| roll_dribbles_completed_5 | 0.0000 |
| roll_dribbles_completed_10 | 0.0000 |
| opp_allows_dribbles_completed_5 | 0.0000 |
| opp_allows_dribbles_completed_10 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.018 | 0.021 | 48 |
| 1 | 0.019 | 0.000 | 47 |
| 2 | 0.019 | 0.021 | 47 |
| 3 | 0.019 | 0.043 | 47 |
| 4 | 0.019 | 0.000 | 48 |
| 5 | 0.019 | 0.021 | 47 |
| 6 | 0.019 | 0.021 | 47 |
| 7 | 0.019 | 0.021 | 47 |
| 8 | 0.019 | 0.000 | 47 |
| 9 | 0.019 | 0.000 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.