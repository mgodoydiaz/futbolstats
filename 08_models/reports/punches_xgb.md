# Predictor de `punches` — resultados

- Filas de test: **472**
- MAE modelo: **0.8342**
- RMSE modelo: **1.0905**
- MAE baseline (rolling 5): **0.8804**
- RMSE baseline (rolling 5): **1.2325**
- Mejora MAE vs baseline: **+5.24%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_punches_10 | 0.1881 |
| roll_punches_3 | 0.1390 |
| is_home | 0.1315 |
| roll_punches_5 | 0.1288 |
| minutes_played | 0.1246 |
| roll_minutes_5 | 0.0989 |
| career_punches | 0.0956 |
| days_rest | 0.0933 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.629 | 0.542 | 48 |
| 1 | 0.664 | 0.596 | 47 |
| 2 | 0.695 | 0.766 | 47 |
| 3 | 0.725 | 0.723 | 47 |
| 4 | 0.745 | 0.596 | 47 |
| 5 | 0.775 | 0.830 | 47 |
| 6 | 0.815 | 1.277 | 47 |
| 7 | 0.862 | 0.681 | 47 |
| 8 | 0.909 | 1.064 | 47 |
| 9 | 1.094 | 1.146 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.