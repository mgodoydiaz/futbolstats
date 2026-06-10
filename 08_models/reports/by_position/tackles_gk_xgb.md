# Predictor de `tackles` — resultados

- Filas de test: **473**
- MAE modelo: **0.0059**
- RMSE modelo: **0.0649**
- MAE baseline (rolling 5): **0.0042**
- RMSE baseline (rolling 5): **0.0650**
- Mejora MAE vs baseline: **-40.55%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.3933 |
| is_home | 0.2415 |
| days_rest | 0.2041 |
| roll_minutes_5 | 0.1612 |
| roll_tackles_5 | 0.0000 |
| roll_tackles_3 | 0.0000 |
| roll_tackles_10 | 0.0000 |
| career_tackles | 0.0000 |
| opp_allows_tackles_5 | 0.0000 |
| opp_allows_tackles_10 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.002 | 0.042 | 48 |
| 1 | 0.002 | 0.000 | 47 |
| 2 | 0.002 | 0.000 | 47 |
| 3 | 0.002 | 0.000 | 47 |
| 4 | 0.002 | 0.000 | 48 |
| 5 | 0.002 | 0.000 | 47 |
| 6 | 0.002 | 0.000 | 47 |
| 7 | 0.002 | 0.000 | 47 |
| 8 | 0.002 | 0.000 | 47 |
| 9 | 0.002 | 0.000 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.