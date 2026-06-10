# Predictor de `key_passes` — resultados

- Filas de test: **473**
- MAE modelo: **0.0524**
- RMSE modelo: **0.1558**
- MAE baseline (rolling 5): **0.0507**
- RMSE baseline (rolling 5): **0.1840**
- Mejora MAE vs baseline: **-3.47%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_key_passes | 0.2170 |
| roll_key_passes_10 | 0.1573 |
| is_home | 0.1397 |
| roll_key_passes_5 | 0.1007 |
| roll_key_passes_3 | 0.0930 |
| roll_minutes_5 | 0.0805 |
| opp_allows_key_passes_10 | 0.0794 |
| minutes_played | 0.0670 |
| days_rest | 0.0654 |
| opp_allows_key_passes_5 | 0.0000 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.014 | 0.000 | 48 |
| 1 | 0.016 | 0.021 | 47 |
| 2 | 0.018 | 0.021 | 47 |
| 3 | 0.018 | 0.000 | 47 |
| 4 | 0.021 | 0.042 | 48 |
| 5 | 0.026 | 0.021 | 47 |
| 6 | 0.030 | 0.021 | 47 |
| 7 | 0.036 | 0.021 | 47 |
| 8 | 0.037 | 0.043 | 47 |
| 9 | 0.076 | 0.062 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.