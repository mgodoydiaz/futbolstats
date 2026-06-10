# Predictor de `shots` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.8258**
- RMSE modelo: **1.1182**
- MAE baseline (rolling 5): **0.9379**
- RMSE baseline (rolling 5): **1.3203**
- Mejora MAE vs baseline: **+11.95%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_shots_5 | 0.2369 |
| career_shots | 0.2092 |
| minutes_played | 0.1989 |
| roll_shots_10 | 0.0882 |
| is_home | 0.0613 |
| roll_shots_3 | 0.0598 |
| roll_minutes_5 | 0.0459 |
| days_rest | 0.0370 |
| opp_allows_shots_10 | 0.0340 |
| opp_allows_shots_5 | 0.0289 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.244 | 0.218 | 216 |
| 1 | 0.431 | 0.454 | 216 |
| 2 | 0.572 | 0.644 | 216 |
| 3 | 0.677 | 0.787 | 216 |
| 4 | 0.782 | 0.796 | 216 |
| 5 | 0.918 | 0.958 | 216 |
| 6 | 1.105 | 1.120 | 216 |
| 7 | 1.283 | 1.222 | 216 |
| 8 | 1.541 | 1.458 | 216 |
| 9 | 2.213 | 2.032 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.