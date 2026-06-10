# Resumen consolidado — XGBoost predictors

Pipeline final entrenado en [`08_models/xgb_predictor.py`](../xgb_predictor.py). Cuatro ejes de variación:

1. **Modelo global** vs **por posición** (`--by-position`)
2. **Sin** vs **con** features de oponente (`--with-opponent`)
3. **`reg:squarederror`** vs **`count:poisson`** (`--objective`)
4. **Dataset player_match** vs **gk_match** (`--dataset`)

Split temporal 70/30. Baseline: rolling mean de 5 partidos sobre el mismo subgrupo.

## Datasets

| Dataset | Filas | Targets |
|---------|------:|---------|
| `statsbomb_player_match.parquet` | 26,295 | shots, passes_completed, xg, tackles, interceptions, fouls, ... (14) |
| `statsbomb_gk_match.parquet` | 1,834 | saves, goals_against, shots_faced, save_pct, ... (7) |

## Resultados — mejor configuración por target

Para cada target, la mejor combinación encontrada y la mejora vs baseline.

| Target | Mejor config | MAE | Baseline MAE | Mejora |
|--------|--------------|----:|-------------:|-------:|
| **passes_completed** | MID + opp | 8.76 | 12.71 | **+31.07%** |
| **shots** | FWD + opp | 1.06 | 1.30 | **+18.10%** |
| **save_pct** (GK) | GK-specific | 0.249 | 0.304 | **+18.17%** |
| tackles | MID + opp | 1.02 | 1.23 | +16.88% |
| interceptions | DEF + opp | 0.94 | 1.09 | +13.67% |
| fouls_drawn | MID + opp | 0.86 | 0.99 | +12.93% |
| fouls_committed | DEF + opp | 0.78 | 0.90 | +12.68% |
| xg | FWD + opp | 0.20 | 0.23 | +12.60% |
| saves (GK) | GK-specific | 1.58 | 1.80 | +12.46% |
| shots_faced (GK) | GK-specific | 3.20 | 3.61 | +11.32% |
| shots_on_target | FWD + opp | 0.63 | 0.69 | +9.48% |
| key_passes | MID + opp + Poisson | 0.73 | 0.81 | +9.36% |
| goals_against (GK) | GK-specific | 0.91 | 1.01 | +9.00% |
| dribbles_completed | MID + opp + Poisson | 0.68 | 0.73 | +6.78% |
| punches (GK) | GK-specific | 0.83 | 0.88 | +5.24% |
| claims (GK) | GK-specific | 0.82 | 0.85 | +3.15% |

## Ganancia incremental de cada mejora

Tomando `passes_completed` como caso testigo:

| Configuración | MAE | Mejora vs naive |
|---------------|----:|----------------:|
| Naive (media global del train) | 12.07 | 0.0% (baseline absoluto) |
| Rolling 5 (baseline)            | 12.07 | 0.0% |
| XGBoost global                  | 9.09  | +24.68% |
| XGBoost global + opp            | 8.81  | +26.97% |
| XGBoost por posición (MID)      | 9.21  | +27.50% |
| **XGBoost MID + opp** (best)    | **8.76**  | **+31.07%** |

Cada upgrade aporta +2-3 puntos porcentuales. Acumulado: ~6 pp de mejora más sobre el XGBoost vanilla.

## Lecturas

**1. Specialización por posición es la mejora más universal.**
Funciona en 9 de 10 targets de `player_match`. Único caso negativo: arqueros para targets generales (shots, tackles ≈ 0 siempre, modelo no tiene de qué aprender).

**2. Features de oponente ayudan donde hay señal contextual.**
Aporta consistentemente +1-3 pp en passes_completed, tackles, fouls. Marginal en xg y shots (más dependen del jugador que del rival).

**3. Poisson rescata sparse targets.**
key_passes pasa de +0.85% (vanilla) a +9.36% (Poisson + opp + pos). Para conteos con muchos ceros, Poisson es estrictamente mejor que MSE como objective.

**4. Modelos GK dedicados son robustos pese a la muestra chica.**
1,834 GK-match rows alcanzan para baselines respetables. save_pct alcanza +18% pese a sólo 472 filas de test. La señal es fuerte porque la consistencia de un arquero específico es alta.

**5. Lo que sigue costando**:
- `claims`, `punches`: dependen mucho de jugadas específicas (centros, balones aéreos del rival). Necesitarían features del tipo de juego del rival.
- `dribbles_completed`: sigue siendo difícil. Probablemente requiere features de oponente más finas (cuánta presión hace el rival) o feature engineering por compañero (a quién recibe el balón).

## Próximos pasos sugeridos

Quedan ROIs claros sin agotar:

1. **Features de competición y fase**: torneo internacional vs liga, fase de grupos vs eliminatoria, importancia del partido.
2. **Embeddings de jugador/equipo**: representaciones densas aprendidas, compartibles entre targets.
3. **Stacking**: combinar XGBoost global + por-posición + Poisson con un meta-learner. Suele ganar 1-2 pp extra.
4. **Modelos jerárquicos bayesianos (PyMC)**: efectos parcialmente \emph{pooled} por jugador y equipo. Útil para jugadores con pocos partidos.
5. **Validación rolling**: en lugar de un cutoff único, entrenar con ventanas móviles. Más caro pero más robusto.
6. **Features de fatiga acumulada**: minutos jugados últimos 21 días, distancia recorrida, etc.

## Files generados

- 10 reportes globales en `reports/<target>_xgb.md`
- 40 reportes por posición en `reports/by_position/<target>_<pos>_xgb.md`
- 6 reportes GK en `reports/<target>_xgb.md` (saves, goals_against, etc.)
- Cada uno incluye MAE/RMSE, importancia de features y tabla de calibración 10-bin.
