# Predictor de `dribbles_completed` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.8220**
- RMSE modelo: **1.1158**
- MAE baseline (rolling 5): **0.8494**
- RMSE baseline (rolling 5): **1.2554**
- Mejora MAE vs baseline: **+3.22%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_dribbles_completed | 0.3035 |
| minutes_played | 0.2636 |
| roll_dribbles_completed_10 | 0.1109 |
| roll_dribbles_completed_5 | 0.0681 |
| roll_minutes_5 | 0.0502 |
| roll_dribbles_completed_3 | 0.0463 |
| opp_allows_dribbles_completed_5 | 0.0459 |
| opp_allows_dribbles_completed_10 | 0.0433 |
| days_rest | 0.0392 |
| is_home | 0.0290 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.196 | 0.120 | 166 |
| 1 | 0.373 | 0.279 | 165 |
| 2 | 0.474 | 0.358 | 165 |
| 3 | 0.595 | 0.479 | 165 |
| 4 | 0.703 | 0.624 | 165 |
| 5 | 0.839 | 0.836 | 165 |
| 6 | 1.013 | 0.891 | 165 |
| 7 | 1.241 | 1.079 | 165 |
| 8 | 1.557 | 1.267 | 165 |
| 9 | 2.541 | 1.994 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.