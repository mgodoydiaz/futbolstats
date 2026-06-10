# Predictor de `fouls_committed` — resultados

- Filas de test: **2,154**
- MAE modelo: **0.7830**
- RMSE modelo: **1.0136**
- MAE baseline (rolling 5): **0.8968**
- RMSE baseline (rolling 5): **1.1869**
- Mejora MAE vs baseline: **+12.68%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_fouls_committed | 0.1796 |
| minutes_played | 0.1629 |
| roll_fouls_committed_10 | 0.1239 |
| is_home | 0.0927 |
| roll_minutes_5 | 0.0871 |
| opp_allows_fouls_committed_10 | 0.0856 |
| days_rest | 0.0686 |
| opp_allows_fouls_committed_5 | 0.0683 |
| roll_fouls_committed_3 | 0.0664 |
| roll_fouls_committed_5 | 0.0649 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.333 | 0.255 | 216 |
| 1 | 0.685 | 0.647 | 215 |
| 2 | 0.792 | 0.679 | 215 |
| 3 | 0.857 | 0.819 | 216 |
| 4 | 0.914 | 0.823 | 215 |
| 5 | 0.970 | 0.953 | 215 |
| 6 | 1.027 | 1.116 | 216 |
| 7 | 1.087 | 1.121 | 215 |
| 8 | 1.165 | 1.321 | 215 |
| 9 | 1.373 | 1.380 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-28 en train; el resto en test.