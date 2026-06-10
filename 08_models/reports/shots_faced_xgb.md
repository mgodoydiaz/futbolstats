# Predictor de `shots_faced` — resultados

- Filas de test: **472**
- MAE modelo: **3.2047**
- RMSE modelo: **4.1149**
- MAE baseline (rolling 5): **3.6137**
- RMSE baseline (rolling 5): **4.7168**
- Mejora MAE vs baseline: **+11.32%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_shots_faced_10 | 0.2024 |
| is_home | 0.2003 |
| minutes_played | 0.1272 |
| career_shots_faced | 0.1268 |
| roll_minutes_5 | 0.1005 |
| roll_shots_faced_5 | 0.0987 |
| roll_shots_faced_3 | 0.0733 |
| days_rest | 0.0707 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 6.690 | 5.562 | 48 |
| 1 | 7.413 | 7.298 | 47 |
| 2 | 7.709 | 8.064 | 47 |
| 3 | 7.874 | 8.532 | 47 |
| 4 | 8.056 | 7.915 | 47 |
| 5 | 8.315 | 8.809 | 47 |
| 6 | 8.833 | 8.447 | 47 |
| 7 | 9.542 | 10.638 | 47 |
| 8 | 10.111 | 9.511 | 47 |
| 9 | 11.310 | 10.729 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.