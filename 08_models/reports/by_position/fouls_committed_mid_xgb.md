# Predictor de `fouls_committed` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.8903**
- RMSE modelo: **1.1289**
- MAE baseline (rolling 5): **1.0021**
- RMSE baseline (rolling 5): **1.3390**
- Mejora MAE vs baseline: **+11.16%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.2914 |
| career_fouls_committed | 0.2212 |
| roll_fouls_committed_10 | 0.0903 |
| roll_fouls_committed_3 | 0.0639 |
| opp_allows_fouls_committed_5 | 0.0594 |
| opp_allows_fouls_committed_10 | 0.0592 |
| roll_minutes_5 | 0.0581 |
| days_rest | 0.0554 |
| roll_fouls_committed_5 | 0.0508 |
| is_home | 0.0502 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.369 | 0.292 | 216 |
| 1 | 0.557 | 0.505 | 216 |
| 2 | 0.784 | 0.722 | 216 |
| 3 | 0.980 | 0.870 | 216 |
| 4 | 1.103 | 1.088 | 216 |
| 5 | 1.238 | 1.264 | 216 |
| 6 | 1.361 | 1.282 | 216 |
| 7 | 1.479 | 1.606 | 216 |
| 8 | 1.636 | 1.588 | 216 |
| 9 | 1.907 | 1.810 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.