# Predictor de `fouls_drawn` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.7736**
- RMSE modelo: **1.0306**
- MAE baseline (rolling 5): **0.8402**
- RMSE baseline (rolling 5): **1.1848**
- Mejora MAE vs baseline: **+7.93%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_fouls_drawn | 0.4201 |
| minutes_played | 0.1514 |
| roll_fouls_drawn_10 | 0.1075 |
| roll_minutes_5 | 0.0936 |
| roll_fouls_drawn_5 | 0.0702 |
| roll_fouls_drawn_3 | 0.0390 |
| is_home | 0.0336 |
| opp_allows_fouls_drawn_5 | 0.0320 |
| days_rest | 0.0265 |
| opp_allows_fouls_drawn_10 | 0.0262 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.261 | 0.196 | 677 |
| 1 | 0.385 | 0.348 | 676 |
| 2 | 0.460 | 0.432 | 676 |
| 3 | 0.580 | 0.540 | 676 |
| 4 | 0.757 | 0.707 | 676 |
| 5 | 0.884 | 0.911 | 676 |
| 6 | 0.999 | 0.886 | 676 |
| 7 | 1.158 | 1.146 | 676 |
| 8 | 1.396 | 1.414 | 676 |
| 9 | 1.975 | 2.030 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.