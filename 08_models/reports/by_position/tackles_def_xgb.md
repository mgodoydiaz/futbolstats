# Predictor de `tackles` — resultados

- Filas de test: **2,154**
- MAE modelo: **1.1790**
- RMSE modelo: **1.5175**
- MAE baseline (rolling 5): **1.3261**
- RMSE baseline (rolling 5): **1.7566**
- Mejora MAE vs baseline: **+11.09%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_tackles | 0.3400 |
| roll_tackles_5 | 0.1408 |
| minutes_played | 0.1291 |
| opp_allows_tackles_5 | 0.0673 |
| roll_tackles_3 | 0.0615 |
| roll_minutes_5 | 0.0588 |
| opp_allows_tackles_10 | 0.0578 |
| roll_tackles_10 | 0.0516 |
| is_home | 0.0483 |
| days_rest | 0.0449 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.592 | 0.468 | 216 |
| 1 | 1.183 | 1.028 | 215 |
| 2 | 1.346 | 1.340 | 215 |
| 3 | 1.436 | 1.519 | 216 |
| 4 | 1.514 | 1.521 | 215 |
| 5 | 1.613 | 1.712 | 215 |
| 6 | 1.748 | 1.806 | 216 |
| 7 | 1.940 | 1.860 | 215 |
| 8 | 2.294 | 2.326 | 215 |
| 9 | 2.911 | 2.731 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.