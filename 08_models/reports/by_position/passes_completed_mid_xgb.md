# Predictor de `passes_completed` — resultados

- Filas de test: **2,160**
- MAE modelo: **8.7605**
- RMSE modelo: **12.3611**
- MAE baseline (rolling 5): **12.7087**
- RMSE baseline (rolling 5): **17.4316**
- Mejora MAE vs baseline: **+31.07%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.3187 |
| career_passes_completed | 0.2538 |
| roll_passes_completed_10 | 0.1282 |
| roll_passes_completed_5 | 0.0865 |
| roll_passes_completed_3 | 0.0520 |
| opp_allows_passes_completed_10 | 0.0452 |
| roll_minutes_5 | 0.0444 |
| opp_allows_passes_completed_5 | 0.0334 |
| is_home | 0.0237 |
| days_rest | 0.0141 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 4.009 | 3.968 | 216 |
| 1 | 8.715 | 9.005 | 216 |
| 2 | 13.811 | 13.481 | 216 |
| 3 | 18.412 | 19.181 | 216 |
| 4 | 22.258 | 23.389 | 216 |
| 5 | 26.341 | 27.375 | 216 |
| 6 | 30.604 | 32.056 | 216 |
| 7 | 35.981 | 36.509 | 216 |
| 8 | 43.627 | 45.412 | 216 |
| 9 | 59.707 | 59.236 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.