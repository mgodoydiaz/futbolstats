# Predictor de `fouls_drawn` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.7010**
- RMSE modelo: **0.8956**
- MAE baseline (rolling 5): **0.7401**
- RMSE baseline (rolling 5): **1.0369**
- Mejora MAE vs baseline: **+5.28%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_fouls_drawn_10 | 0.2447 |
| career_fouls_drawn | 0.1718 |
| minutes_played | 0.1351 |
| roll_fouls_drawn_3 | 0.0846 |
| opp_allows_fouls_drawn_10 | 0.0704 |
| roll_fouls_drawn_5 | 0.0687 |
| days_rest | 0.0665 |
| roll_minutes_5 | 0.0571 |
| opp_allows_fouls_drawn_5 | 0.0522 |
| is_home | 0.0488 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.220 | 0.204 | 216 |
| 1 | 0.455 | 0.391 | 215 |
| 2 | 0.543 | 0.479 | 215 |
| 3 | 0.599 | 0.519 | 216 |
| 4 | 0.659 | 0.665 | 215 |
| 5 | 0.712 | 0.651 | 215 |
| 6 | 0.787 | 0.824 | 216 |
| 7 | 0.862 | 0.865 | 215 |
| 8 | 0.990 | 0.907 | 215 |
| 9 | 1.255 | 1.245 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.