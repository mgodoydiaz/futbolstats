# Predictor de `claims` — resultados

- Filas de test: **472**
- MAE modelo: **0.8234**
- RMSE modelo: **0.9892**
- MAE baseline (rolling 5): **0.8502**
- RMSE baseline (rolling 5): **1.1302**
- Mejora MAE vs baseline: **+3.15%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_claims | 0.1997 |
| roll_claims_10 | 0.1700 |
| roll_claims_3 | 0.1369 |
| roll_claims_5 | 0.1335 |
| roll_minutes_5 | 0.0935 |
| minutes_played | 0.0934 |
| days_rest | 0.0924 |
| is_home | 0.0806 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.701 | 0.562 | 48 |
| 1 | 0.808 | 0.426 | 47 |
| 2 | 0.863 | 0.787 | 47 |
| 3 | 0.898 | 0.915 | 47 |
| 4 | 0.939 | 0.809 | 47 |
| 5 | 0.975 | 0.660 | 47 |
| 6 | 1.012 | 0.638 | 47 |
| 7 | 1.048 | 0.745 | 47 |
| 8 | 1.126 | 0.766 | 47 |
| 9 | 1.562 | 0.979 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.