# Predictor de `shots_on_target` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.2333**
- RMSE modelo: **0.3635**
- MAE baseline (rolling 5): **0.2203**
- RMSE baseline (rolling 5): **0.4384**
- Mejora MAE vs baseline: **-5.90%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.1789 |
| career_shots_on_target | 0.1554 |
| roll_shots_on_target_10 | 0.1295 |
| roll_shots_on_target_3 | 0.1003 |
| opp_allows_shots_on_target_5 | 0.0875 |
| days_rest | 0.0789 |
| opp_allows_shots_on_target_10 | 0.0777 |
| roll_shots_on_target_5 | 0.0701 |
| roll_minutes_5 | 0.0636 |
| is_home | 0.0581 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.078 | 0.069 | 216 |
| 1 | 0.105 | 0.102 | 215 |
| 2 | 0.121 | 0.074 | 215 |
| 3 | 0.128 | 0.106 | 216 |
| 4 | 0.136 | 0.126 | 215 |
| 5 | 0.144 | 0.140 | 215 |
| 6 | 0.161 | 0.093 | 216 |
| 7 | 0.171 | 0.126 | 215 |
| 8 | 0.181 | 0.121 | 215 |
| 9 | 0.255 | 0.259 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.