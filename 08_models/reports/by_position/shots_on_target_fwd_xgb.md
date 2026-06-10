# Predictor de `shots_on_target` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.6266**
- RMSE modelo: **0.8296**
- MAE baseline (rolling 5): **0.6913**
- RMSE baseline (rolling 5): **0.9749**
- Mejora MAE vs baseline: **+9.36%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.3506 |
| career_shots_on_target | 0.1552 |
| roll_shots_on_target_10 | 0.1064 |
| roll_shots_on_target_3 | 0.0722 |
| is_home | 0.0658 |
| roll_minutes_5 | 0.0602 |
| roll_shots_on_target_5 | 0.0526 |
| days_rest | 0.0484 |
| opp_allows_shots_on_target_10 | 0.0456 |
| opp_allows_shots_on_target_5 | 0.0430 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.176 | 0.163 | 166 |
| 1 | 0.270 | 0.279 | 165 |
| 2 | 0.349 | 0.321 | 165 |
| 3 | 0.416 | 0.545 | 165 |
| 4 | 0.479 | 0.533 | 165 |
| 5 | 0.567 | 0.636 | 165 |
| 6 | 0.741 | 0.624 | 165 |
| 7 | 0.855 | 0.782 | 165 |
| 8 | 0.981 | 0.824 | 165 |
| 9 | 1.242 | 1.452 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.