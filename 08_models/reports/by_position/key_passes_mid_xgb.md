# Predictor de `key_passes` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.7316**
- RMSE modelo: **1.0100**
- MAE baseline (rolling 5): **0.8071**
- RMSE baseline (rolling 5): **1.1860**
- Mejora MAE vs baseline: **+9.36%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_key_passes_5 | 0.2379 |
| minutes_played | 0.2268 |
| career_key_passes | 0.1883 |
| roll_key_passes_10 | 0.0815 |
| is_home | 0.0683 |
| opp_allows_key_passes_5 | 0.0460 |
| opp_allows_key_passes_10 | 0.0427 |
| roll_minutes_5 | 0.0403 |
| roll_key_passes_3 | 0.0371 |
| days_rest | 0.0310 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.171 | 0.125 | 216 |
| 1 | 0.303 | 0.241 | 216 |
| 2 | 0.421 | 0.398 | 216 |
| 3 | 0.532 | 0.560 | 216 |
| 4 | 0.639 | 0.588 | 216 |
| 5 | 0.731 | 0.852 | 216 |
| 6 | 0.846 | 0.907 | 216 |
| 7 | 0.992 | 1.102 | 216 |
| 8 | 1.229 | 1.144 | 216 |
| 9 | 1.989 | 1.773 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.