# Predictor de `save_pct` — resultados

- Filas de test: **472**
- MAE modelo: **0.2487**
- RMSE modelo: **0.3948**
- MAE baseline (rolling 5): **0.3039**
- RMSE baseline (rolling 5): **0.4681**
- Mejora MAE vs baseline: **+18.17%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.1937 |
| roll_save_pct_3 | 0.1715 |
| roll_save_pct_10 | 0.1470 |
| roll_minutes_5 | 0.1432 |
| roll_save_pct_5 | 0.1221 |
| career_save_pct | 0.0960 |
| is_home | 0.0780 |
| days_rest | 0.0486 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.396 | 0.327 | 48 |
| 1 | 0.399 | 0.459 | 47 |
| 2 | 0.402 | 0.357 | 47 |
| 3 | 0.403 | 0.508 | 47 |
| 4 | 0.403 | 0.389 | 47 |
| 5 | 0.404 | 0.347 | 47 |
| 6 | 0.406 | 0.380 | 47 |
| 7 | 0.412 | 0.299 | 47 |
| 8 | 0.418 | 0.426 | 47 |
| 9 | 0.436 | 0.359 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.