# Predictor de `passes_completed` — resultados

- Filas de test: **473**
- MAE modelo: **5.8946**
- RMSE modelo: **7.6831**
- MAE baseline (rolling 5): **6.3360**
- RMSE baseline (rolling 5): **8.1126**
- Mejora MAE vs baseline: **+6.97%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_passes_completed_5 | 0.2809 |
| career_passes_completed | 0.1848 |
| roll_passes_completed_10 | 0.1217 |
| roll_passes_completed_3 | 0.1061 |
| minutes_played | 0.0895 |
| opp_allows_passes_completed_10 | 0.0580 |
| opp_allows_passes_completed_5 | 0.0544 |
| days_rest | 0.0404 |
| is_home | 0.0322 |
| roll_minutes_5 | 0.0322 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 13.984 | 13.938 | 48 |
| 1 | 15.188 | 17.234 | 47 |
| 2 | 16.481 | 17.191 | 47 |
| 3 | 17.866 | 18.702 | 47 |
| 4 | 19.054 | 20.792 | 48 |
| 5 | 20.032 | 21.681 | 47 |
| 6 | 21.273 | 22.489 | 47 |
| 7 | 22.779 | 25.362 | 47 |
| 8 | 24.887 | 26.234 | 47 |
| 9 | 28.913 | 27.292 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.