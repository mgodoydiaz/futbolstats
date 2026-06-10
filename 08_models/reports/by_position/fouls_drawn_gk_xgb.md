# Predictor de `fouls_drawn` — resultados

- Filas de test: **473**
- MAE modelo: **0.2678**
- RMSE modelo: **0.4224**
- MAE baseline (rolling 5): **0.2413**
- RMSE baseline (rolling 5): **0.4816**
- Mejora MAE vs baseline: **-10.99%** (↑ peor)

## Importancia de features (XGBoost gain)

| Feature | Importancia |
|---------|------------:|
| roll_fouls_drawn_3 | 0.1701 |
| minutes_played | 0.1412 |
| is_home | 0.0993 |
| roll_minutes_5 | 0.0943 |
| career_fouls_drawn | 0.0940 |
| opp_allows_fouls_drawn_5 | 0.0919 |
| opp_allows_fouls_drawn_10 | 0.0873 |
| roll_fouls_drawn_5 | 0.0846 |
| days_rest | 0.0738 |
| roll_fouls_drawn_10 | 0.0636 |

## Tabla de calibración (10 bins por predicción)

| Bin | Predicho (media) | Observado (media) | n |
|----:|-----------------:|------------------:|--:|
| 0 | 0.106 | 0.062 | 48 |
| 1 | 0.118 | 0.106 | 47 |
| 2 | 0.127 | 0.043 | 47 |
| 3 | 0.133 | 0.213 | 47 |
| 4 | 0.142 | 0.125 | 48 |
| 5 | 0.153 | 0.170 | 47 |
| 6 | 0.163 | 0.255 | 47 |
| 7 | 0.172 | 0.170 | 47 |
| 8 | 0.187 | 0.106 | 47 |
| 9 | 0.247 | 0.312 | 48 |

Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.

Cutoff temporal: filas con fecha $\leq$ 2022-01-02 en train; el resto en test.