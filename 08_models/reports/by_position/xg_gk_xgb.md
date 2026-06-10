# Predictor de `xg` — resultados

- Filas de test: **473**
- MAE modelo: **0.0038**
- RMSE modelo: **0.0510**
- MAE baseline (rolling 5): **0.0041**
- RMSE baseline (rolling 5): **0.0520**
- Mejora MAE vs baseline: **+8.92%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| is_home | 0.3155 |
| roll_minutes_5 | 0.2897 |
| minutes_played | 0.2348 |
| days_rest | 0.1600 |
| roll_xg_5 | 0.0000 |
| roll_xg_3 | 0.0000 |
| roll_xg_10 | 0.0000 |
| career_xg | 0.0000 |
| opp_allows_xg_5 | 0.0000 |
| opp_allows_xg_10 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.000 | 0.016 | 48 |
| 1 | 0.000 | 0.000 | 47 |
| 2 | 0.000 | 0.000 | 47 |
| 3 | 0.000 | 0.000 | 47 |
| 4 | 0.000 | 0.000 | 48 |
| 5 | 0.000 | 0.000 | 47 |
| 6 | 0.000 | 0.000 | 47 |
| 7 | 0.000 | 0.000 | 47 |
| 8 | 0.000 | 0.000 | 47 |
| 9 | 0.002 | 0.018 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.