# Predictor de `interceptions` — resultados

- Filas de test: **2,160**
- MAE modelo: **0.7821**
- RMSE modelo: **0.9951**
- MAE baseline (rolling 5): **0.8439**
- RMSE baseline (rolling 5): **1.1585**
- Mejora MAE vs baseline: **+7.32%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_interceptions_5 | 0.2280 |
| minutes_played | 0.2118 |
| roll_interceptions_10 | 0.1205 |
| opp_allows_interceptions_5 | 0.0970 |
| roll_interceptions_3 | 0.0786 |
| career_interceptions | 0.0752 |
| opp_allows_interceptions_10 | 0.0630 |
| is_home | 0.0468 |
| days_rest | 0.0408 |
| roll_minutes_5 | 0.0383 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.295 | 0.185 | 216 |
| 1 | 0.438 | 0.310 | 216 |
| 2 | 0.582 | 0.458 | 216 |
| 3 | 0.728 | 0.611 | 216 |
| 4 | 0.856 | 0.759 | 216 |
| 5 | 1.007 | 0.898 | 216 |
| 6 | 1.154 | 1.037 | 216 |
| 7 | 1.292 | 1.042 | 216 |
| 8 | 1.438 | 1.171 | 216 |
| 9 | 1.839 | 1.653 | 216 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-11 en train; el resto en test.