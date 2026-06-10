# Predictor de `interceptions` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.9421**
- RMSE modelo: **1.2374**
- MAE baseline (rolling 5): **1.0913**
- RMSE baseline (rolling 5): **1.4706**
- Mejora MAE vs baseline: **+13.67%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| opp_allows_interceptions_5 | 0.2778 |
| minutes_played | 0.1382 |
| roll_interceptions_3 | 0.1208 |
| roll_interceptions_5 | 0.1052 |
| roll_interceptions_10 | 0.0783 |
| career_interceptions | 0.0672 |
| opp_allows_interceptions_10 | 0.0654 |
| days_rest | 0.0603 |
| roll_minutes_5 | 0.0464 |
| is_home | 0.0405 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.419 | 0.218 | 216 |
| 1 | 0.847 | 0.884 | 215 |
| 2 | 1.038 | 1.060 | 215 |
| 3 | 1.124 | 0.991 | 216 |
| 4 | 1.222 | 1.065 | 215 |
| 5 | 1.345 | 1.228 | 215 |
| 6 | 1.466 | 1.181 | 216 |
| 7 | 1.620 | 1.493 | 215 |
| 8 | 1.831 | 1.623 | 215 |
| 9 | 2.188 | 2.065 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.