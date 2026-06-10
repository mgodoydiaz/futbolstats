# Predictor de `interceptions` — resultados

- Filas de test: **6,761**
- MAE modelo: **0.7347**
- RMSE modelo: **0.9950**
- MAE baseline (rolling 5): **0.7701**
- RMSE baseline (rolling 5): **1.1452**
- Mejora MAE vs baseline: **+4.60%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_interceptions_5 | 0.4170 |
| roll_interceptions_10 | 0.1407 |
| career_interceptions | 0.1209 |
| minutes_played | 0.0883 |
| roll_interceptions_3 | 0.0813 |
| opp_allows_interceptions_5 | 0.0687 |
| roll_minutes_5 | 0.0273 |
| days_rest | 0.0219 |
| opp_allows_interceptions_10 | 0.0204 |
| is_home | 0.0135 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.240 | 0.136 | 677 |
| 1 | 0.332 | 0.244 | 676 |
| 2 | 0.376 | 0.262 | 676 |
| 3 | 0.495 | 0.479 | 676 |
| 4 | 0.661 | 0.589 | 676 |
| 5 | 0.847 | 0.774 | 676 |
| 6 | 1.007 | 0.941 | 676 |
| 7 | 1.180 | 1.075 | 676 |
| 8 | 1.450 | 1.213 | 676 |
| 9 | 1.895 | 1.811 | 676 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-23 en train; el resto en test.