# Predictor de `interceptions` — resultados

- Filas de test: **1,652**
- MAE modelo: **0.5191**
- RMSE modelo: **0.6611**
- MAE baseline (rolling 5): **0.4974**
- RMSE baseline (rolling 5): **0.7698**
- Mejora MAE vs baseline: **-4.36%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| minutes_played | 0.1923 |
| roll_interceptions_10 | 0.1661 |
| career_interceptions | 0.1540 |
| roll_interceptions_5 | 0.0979 |
| opp_allows_interceptions_5 | 0.0820 |
| opp_allows_interceptions_10 | 0.0700 |
| roll_interceptions_3 | 0.0695 |
| days_rest | 0.0646 |
| roll_minutes_5 | 0.0573 |
| is_home | 0.0464 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.216 | 0.102 | 166 |
| 1 | 0.251 | 0.121 | 165 |
| 2 | 0.277 | 0.242 | 165 |
| 3 | 0.325 | 0.273 | 165 |
| 4 | 0.354 | 0.230 | 165 |
| 5 | 0.408 | 0.352 | 165 |
| 6 | 0.490 | 0.382 | 165 |
| 7 | 0.581 | 0.545 | 165 |
| 8 | 0.638 | 0.673 | 165 |
| 9 | 0.728 | 0.657 | 166 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-25 en train; el resto en test.