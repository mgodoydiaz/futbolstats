# Predictor de `goals_against` — resultados

- Filas de test: **472**
- MAE modelo: **0.9148**
- RMSE modelo: **1.1847**
- MAE baseline (rolling 5): **1.0053**
- RMSE baseline (rolling 5): **1.3629**
- Mejora MAE vs baseline: **+9.00%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_goals_against_5 | 0.1489 |
| career_goals_against | 0.1487 |
| roll_goals_against_10 | 0.1343 |
| days_rest | 0.1224 |
| roll_minutes_5 | 0.1220 |
| minutes_played | 0.1132 |
| is_home | 0.1115 |
| roll_goals_against_3 | 0.0989 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 1.077 | 0.604 | 48 |
| 1 | 1.152 | 1.404 | 47 |
| 2 | 1.175 | 1.106 | 47 |
| 3 | 1.181 | 1.043 | 47 |
| 4 | 1.191 | 1.000 | 47 |
| 5 | 1.210 | 1.064 | 47 |
| 6 | 1.231 | 0.915 | 47 |
| 7 | 1.261 | 1.064 | 47 |
| 8 | 1.299 | 1.404 | 47 |
| 9 | 1.372 | 1.458 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.