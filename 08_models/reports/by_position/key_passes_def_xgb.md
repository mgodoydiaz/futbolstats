# Predictor de `key_passes` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.5279**
- RMSE modelo: **0.7369**
- MAE baseline (rolling 5): **0.5242**
- RMSE baseline (rolling 5): **0.8400**
- Mejora MAE vs baseline: **-0.72%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_key_passes | 0.3512 |
| roll_key_passes_10 | 0.1948 |
| roll_key_passes_5 | 0.1115 |
| minutes_played | 0.0731 |
| roll_key_passes_3 | 0.0703 |
| is_home | 0.0450 |
| opp_allows_key_passes_5 | 0.0419 |
| days_rest | 0.0379 |
| roll_minutes_5 | 0.0374 |
| opp_allows_key_passes_10 | 0.0370 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.155 | 0.148 | 216 |
| 1 | 0.249 | 0.274 | 215 |
| 2 | 0.257 | 0.200 | 215 |
| 3 | 0.270 | 0.231 | 216 |
| 4 | 0.288 | 0.330 | 215 |
| 5 | 0.319 | 0.363 | 215 |
| 6 | 0.406 | 0.361 | 216 |
| 7 | 0.565 | 0.567 | 215 |
| 8 | 0.716 | 0.674 | 215 |
| 9 | 0.979 | 0.972 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.