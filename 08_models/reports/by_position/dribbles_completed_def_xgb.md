# Predictor de `dribbles_completed` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.4929**
- RMSE modelo: **0.6620**
- MAE baseline (rolling 5): **0.4709**
- RMSE baseline (rolling 5): **0.7758**
- Mejora MAE vs baseline: **-4.68%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_dribbles_completed | 0.3675 |
| roll_dribbles_completed_10 | 0.1548 |
| minutes_played | 0.0856 |
| roll_dribbles_completed_5 | 0.0784 |
| opp_allows_dribbles_completed_10 | 0.0607 |
| roll_minutes_5 | 0.0571 |
| roll_dribbles_completed_3 | 0.0552 |
| opp_allows_dribbles_completed_5 | 0.0484 |
| is_home | 0.0468 |
| days_rest | 0.0455 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.093 | 0.097 | 216 |
| 1 | 0.241 | 0.167 | 215 |
| 2 | 0.270 | 0.209 | 215 |
| 3 | 0.285 | 0.208 | 216 |
| 4 | 0.302 | 0.242 | 215 |
| 5 | 0.333 | 0.400 | 215 |
| 6 | 0.381 | 0.306 | 216 |
| 7 | 0.451 | 0.395 | 215 |
| 8 | 0.663 | 0.619 | 215 |
| 9 | 1.023 | 0.815 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.