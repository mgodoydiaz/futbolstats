# Predictor de `saves` — resultados

- Filas de test: **472**
- MAE modelo: **1.5765**
- RMSE modelo: **2.0304**
- MAE baseline (rolling 5): **1.8009**
- RMSE baseline (rolling 5): **2.3473**
- Mejora MAE vs baseline: **+12.46%** (↓ mejor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| career_saves | 0.1465 |
| is_home | 0.1437 |
| roll_saves_5 | 0.1429 |
| minutes_played | 0.1216 |
| days_rest | 0.1206 |
| roll_saves_10 | 0.1141 |
| roll_saves_3 | 0.1082 |
| roll_minutes_5 | 0.1023 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 2.509 | 2.500 | 48 |
| 1 | 2.651 | 2.383 | 47 |
| 2 | 2.703 | 2.426 | 47 |
| 3 | 2.738 | 2.830 | 47 |
| 4 | 2.764 | 3.000 | 47 |
| 5 | 2.798 | 3.106 | 47 |
| 6 | 2.830 | 2.723 | 47 |
| 7 | 2.899 | 2.702 | 47 |
| 8 | 3.020 | 3.702 | 47 |
| 9 | 3.335 | 3.125 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.