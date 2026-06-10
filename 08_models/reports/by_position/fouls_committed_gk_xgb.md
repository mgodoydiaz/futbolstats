# Predictor de `fouls_committed` — resultados

- Filas de test: **473**
- MAE modelo: **0.0418**
- RMSE modelo: **0.1500**
- MAE baseline (rolling 5): **0.0462**
- RMSE baseline (rolling 5): **0.1774**
- Mejora MAE vs baseline: **+9.55%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.1824 |
| roll_minutes_5 | 0.1474 |
| career_fouls_committed | 0.1161 |
| opp_allows_fouls_committed_5 | 0.1108 |
| opp_allows_fouls_committed_10 | 0.0988 |
| is_home | 0.0966 |
| days_rest | 0.0953 |
| roll_fouls_committed_3 | 0.0770 |
| roll_fouls_committed_10 | 0.0739 |
| roll_fouls_committed_5 | 0.0017 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.012 | 0.021 | 48 |
| 1 | 0.013 | 0.000 | 47 |
| 2 | 0.014 | 0.000 | 47 |
| 3 | 0.015 | 0.021 | 47 |
| 4 | 0.016 | 0.021 | 48 |
| 5 | 0.018 | 0.021 | 47 |
| 6 | 0.020 | 0.021 | 47 |
| 7 | 0.020 | 0.021 | 47 |
| 8 | 0.024 | 0.043 | 47 |
| 9 | 0.045 | 0.062 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.