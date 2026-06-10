# Predictor de `key_passes` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.6308**
- RMSE modelo: **0.8668**
- MAE baseline (rolling 5): **0.6447**
- RMSE baseline (rolling 5): **0.9941**
- Mejora MAE vs baseline: **+2.15%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_key_passes | 0.3713 |
| roll_key_passes_10 | 0.1550 |
| roll_key_passes_5 | 0.1406 |
| minutes_played | 0.1005 |
| opp_allows_key_passes_10 | 0.0516 |
| roll_key_passes_3 | 0.0500 |
| is_home | 0.0436 |
| roll_minutes_5 | 0.0402 |
| opp_allows_key_passes_5 | 0.0295 |
| days_rest | 0.0177 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.191 | 0.129 | 677 |
| 1 | 0.222 | 0.169 | 676 |
| 2 | 0.280 | 0.269 | 676 |
| 3 | 0.368 | 0.302 | 676 |
| 4 | 0.458 | 0.484 | 676 |
| 5 | 0.551 | 0.494 | 676 |
| 6 | 0.680 | 0.673 | 676 |
| 7 | 0.844 | 0.859 | 676 |
| 8 | 1.028 | 1.044 | 676 |
| 9 | 1.634 | 1.527 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.