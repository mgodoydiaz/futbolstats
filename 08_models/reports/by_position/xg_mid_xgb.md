# Predictor de `xg` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.1111**
- RMSE modelo: **0.2023**
- MAE baseline (rolling 5): **0.1241**
- RMSE baseline (rolling 5): **0.2343**
- Mejora MAE vs baseline: **+10.47%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_xg | 0.1919 |
| minutes_played | 0.1413 |
| roll_xg_5 | 0.1210 |
| roll_xg_10 | 0.1050 |
| opp_allows_xg_5 | 0.0960 |
| days_rest | 0.0827 |
| roll_xg_3 | 0.0767 |
| roll_minutes_5 | 0.0736 |
| opp_allows_xg_10 | 0.0676 |
| is_home | 0.0442 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.030 | 0.032 | 216 |
| 1 | 0.040 | 0.076 | 216 |
| 2 | 0.047 | 0.076 | 216 |
| 3 | 0.055 | 0.072 | 216 |
| 4 | 0.063 | 0.053 | 216 |
| 5 | 0.074 | 0.081 | 216 |
| 6 | 0.090 | 0.088 | 216 |
| 7 | 0.112 | 0.106 | 216 |
| 8 | 0.145 | 0.176 | 216 |
| 9 | 0.259 | 0.241 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.