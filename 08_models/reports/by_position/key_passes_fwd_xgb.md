# Predictor de `key_passes` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.7343**
- RMSE modelo: **0.9815**
- MAE baseline (rolling 5): **0.7987**
- RMSE baseline (rolling 5): **1.1368**
- Mejora MAE vs baseline: **+8.06%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.3428 |
| career_key_passes | 0.1741 |
| roll_key_passes_10 | 0.1728 |
| roll_key_passes_5 | 0.0588 |
| is_home | 0.0532 |
| opp_allows_key_passes_10 | 0.0455 |
| opp_allows_key_passes_5 | 0.0422 |
| roll_minutes_5 | 0.0394 |
| days_rest | 0.0369 |
| roll_key_passes_3 | 0.0344 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.185 | 0.151 | 166 |
| 1 | 0.355 | 0.230 | 165 |
| 2 | 0.436 | 0.358 | 165 |
| 3 | 0.499 | 0.533 | 165 |
| 4 | 0.599 | 0.739 | 165 |
| 5 | 0.802 | 0.818 | 165 |
| 6 | 0.951 | 1.000 | 165 |
| 7 | 1.091 | 1.085 | 165 |
| 8 | 1.271 | 1.352 | 165 |
| 9 | 1.851 | 1.404 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.