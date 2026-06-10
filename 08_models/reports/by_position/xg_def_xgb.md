# Predictor de `xg` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.0689**
- RMSE modelo: **0.1328**
- MAE baseline (rolling 5): **0.0729**
- RMSE baseline (rolling 5): **0.1542**
- Mejora MAE vs baseline: **+5.56%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.1534 |
| career_xg | 0.1523 |
| roll_xg_3 | 0.1219 |
| roll_minutes_5 | 0.1098 |
| roll_xg_5 | 0.0954 |
| opp_allows_xg_5 | 0.0934 |
| roll_xg_10 | 0.0887 |
| days_rest | 0.0763 |
| opp_allows_xg_10 | 0.0631 |
| is_home | 0.0457 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.024 | 0.030 | 216 |
| 1 | 0.030 | 0.032 | 215 |
| 2 | 0.032 | 0.024 | 215 |
| 3 | 0.033 | 0.037 | 216 |
| 4 | 0.036 | 0.028 | 215 |
| 5 | 0.041 | 0.045 | 215 |
| 6 | 0.046 | 0.056 | 216 |
| 7 | 0.058 | 0.058 | 215 |
| 8 | 0.066 | 0.047 | 215 |
| 9 | 0.147 | 0.144 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.