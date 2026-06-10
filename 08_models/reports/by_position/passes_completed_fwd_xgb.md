# Predictor de `passes_completed` — resultados

- Filas de test: **1,652**
- MAE modelo: **4.6930**
- RMSE modelo: **6.6747**
- MAE baseline (rolling 5): **6.5051**
- RMSE baseline (rolling 5): **9.0856**
- Mejora MAE vs baseline: **+27.86%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.3137 |
| career_passes_completed | 0.2098 |
| roll_passes_completed_5 | 0.1872 |
| roll_passes_completed_10 | 0.0898 |
| roll_passes_completed_3 | 0.0631 |
| roll_minutes_5 | 0.0418 |
| opp_allows_passes_completed_5 | 0.0257 |
| opp_allows_passes_completed_10 | 0.0248 |
| is_home | 0.0247 |
| days_rest | 0.0192 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 2.549 | 2.211 | 166 |
| 1 | 5.022 | 3.909 | 165 |
| 2 | 7.031 | 6.133 | 165 |
| 3 | 9.555 | 8.424 | 165 |
| 4 | 11.839 | 11.194 | 165 |
| 5 | 13.749 | 12.909 | 165 |
| 6 | 15.534 | 15.012 | 165 |
| 7 | 17.831 | 17.673 | 165 |
| 8 | 21.141 | 21.733 | 165 |
| 9 | 31.072 | 30.277 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.