# Predictor de `interceptions` — resultados

- Filas de test: **473**
- MAE modelo: **0.0014**
- RMSE modelo: **0.0015**
- MAE baseline (rolling 5): **0.0000**
- RMSE baseline (rolling 5): **0.0000**
- Mejora MAE vs baseline: **+0.00%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| is_home | 0.3644 |
| roll_minutes_5 | 0.2403 |
| days_rest | 0.2257 |
| minutes_played | 0.1696 |
| roll_interceptions_5 | 0.0000 |
| roll_interceptions_3 | 0.0000 |
| roll_interceptions_10 | 0.0000 |
| career_interceptions | 0.0000 |
| opp_allows_interceptions_5 | 0.0000 |
| opp_allows_interceptions_10 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.001 | 0.000 | 48 |
| 1 | 0.001 | 0.000 | 47 |
| 2 | 0.001 | 0.000 | 47 |
| 3 | 0.001 | 0.000 | 47 |
| 4 | 0.001 | 0.000 | 48 |
| 5 | 0.001 | 0.000 | 47 |
| 6 | 0.001 | 0.000 | 47 |
| 7 | 0.001 | 0.000 | 47 |
| 8 | 0.001 | 0.000 | 47 |
| 9 | 0.002 | 0.000 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.