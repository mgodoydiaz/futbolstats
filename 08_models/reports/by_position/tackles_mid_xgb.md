# Predictor de `tackles` — resultados

- Filas de test: **2,160**
- MAE modelo: **1.0223**
- RMSE modelo: **1.3437**
- MAE baseline (rolling 5): **1.2299**
- RMSE baseline (rolling 5): **1.6391**
- Mejora MAE vs baseline: **+16.88%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2971 |
| career_tackles | 0.2070 |
| roll_tackles_10 | 0.1817 |
| opp_allows_tackles_5 | 0.0572 |
| roll_tackles_5 | 0.0516 |
| roll_tackles_3 | 0.0510 |
| roll_minutes_5 | 0.0502 |
| opp_allows_tackles_10 | 0.0425 |
| is_home | 0.0347 |
| days_rest | 0.0270 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.392 | 0.306 | 216 |
| 1 | 0.665 | 0.593 | 216 |
| 2 | 0.941 | 0.755 | 216 |
| 3 | 1.238 | 1.204 | 216 |
| 4 | 1.459 | 1.398 | 216 |
| 5 | 1.626 | 1.560 | 216 |
| 6 | 1.779 | 1.824 | 216 |
| 7 | 2.014 | 1.889 | 216 |
| 8 | 2.305 | 2.019 | 216 |
| 9 | 2.857 | 2.769 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.