# Predictor de `fouls_committed` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.7826**
- RMSE modelo: **1.0139**
- MAE baseline (rolling 5): **0.8791**
- RMSE baseline (rolling 5): **1.2008**
- Mejora MAE vs baseline: **+10.97%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2798 |
| career_fouls_committed | 0.1278 |
| roll_fouls_committed_10 | 0.1236 |
| roll_fouls_committed_3 | 0.0967 |
| roll_minutes_5 | 0.0787 |
| opp_allows_fouls_committed_10 | 0.0656 |
| days_rest | 0.0618 |
| roll_fouls_committed_5 | 0.0616 |
| opp_allows_fouls_committed_5 | 0.0615 |
| is_home | 0.0430 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.273 | 0.301 | 166 |
| 1 | 0.500 | 0.382 | 165 |
| 2 | 0.630 | 0.527 | 165 |
| 3 | 0.748 | 0.721 | 165 |
| 4 | 0.867 | 0.867 | 165 |
| 5 | 0.958 | 0.848 | 165 |
| 6 | 1.040 | 1.133 | 165 |
| 7 | 1.138 | 1.127 | 165 |
| 8 | 1.275 | 1.261 | 165 |
| 9 | 1.574 | 1.572 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.