# Predictor de `passes_completed` — resultados

- Filas de test: **6,761**
- MAE modelo: **8.8125**
- RMSE modelo: **12.9390**
- MAE baseline (rolling 5): **12.0675**
- RMSE baseline (rolling 5): **17.3065**
- Mejora MAE vs baseline: **+26.97%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_passes_completed | 0.2767 |
| roll_passes_completed_10 | 0.2702 |
| roll_passes_completed_5 | 0.1843 |
| minutes_played | 0.1315 |
| roll_passes_completed_3 | 0.0316 |
| roll_minutes_5 | 0.0289 |
| opp_allows_passes_completed_10 | 0.0288 |
| opp_allows_passes_completed_5 | 0.0233 |
| is_home | 0.0161 |
| days_rest | 0.0086 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 3.969 | 3.244 | 677 |
| 1 | 8.562 | 7.762 | 676 |
| 2 | 13.252 | 12.138 | 676 |
| 3 | 16.903 | 17.121 | 676 |
| 4 | 20.369 | 20.908 | 676 |
| 5 | 24.534 | 25.373 | 676 |
| 6 | 29.621 | 30.641 | 676 |
| 7 | 35.902 | 37.240 | 676 |
| 8 | 44.415 | 44.784 | 676 |
| 9 | 60.836 | 61.362 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.