# 08_models — Modelos predictivos

Modelos de regresión que predicen **estadísticas individuales por partido** (no resultados).

## Targets prioritarios

| Target | Fuente de datos | Notas |
|--------|-----------------|-------|
| `shots` | FBref match summary | Core target |
| `shots_on_target` | FBref match summary | Subset de shots |
| `passes_completed` | FBref match summary | Requiere match-level scrape |
| `passes_attempted` | FBref match summary | |
| `key_passes` | FBref match summary | |
| `tackles` | FBref match summary | |
| `interceptions` | FBref match summary | |
| `dribbles` | FBref match summary | |
| `xG` | FBref match summary o StatsBomb | StatsBomb tiene mejor calidad |

## Estructura propuesta por modelo

```
08_models/
└── <target>_predictor/
    ├── features.py         # build feature matrix from 02_data_processed/
    ├── train.py            # train + save model
    ├── evaluate.py         # MAE / RMSE / calibration
    ├── predict.py          # load model, score new fixtures
    └── README.md           # what features, what algo, version log
```

## Filosofía

- **Una sola observación = un jugador en un partido**. Las features describen contexto previo al partido; el target es la stat de ese partido.
- **Splits temporales**: entrenar con T-2 temporadas, validar con T-1, testear con T. Nunca random shuffle (data leak).
- **Features deben estar disponibles antes del kickoff** — no usar minutos jugados como feature para predecir shots, por ejemplo. Sí usar "minutos promedio últimos 5 partidos".

## Features candidatas

**Player**
- Rolling avg de stats (últimos 5, 10, 20 partidos)
- Lugar en alineación (titular vs suplente últimos 5)
- Días de descanso desde último partido
- Edad
- Posición (one-hot o embedding)

**Match context**
- Local / visitante
- Fortaleza del rival (rolling avg de la stat opuesta concedida por el rival)
- Importancia del partido (liga vs copa, jornada del calendario)

**Team**
- Forma del equipo (puntos últimos 5)
- Estilo (posesión promedio, PPDA — requiere features futuros)

## Modelos

1. **Baseline**: media histórica del jugador para esa stat. Sin features. Da el piso.
2. **Linear**: regresión Ridge sobre features numéricas. Interpretable.
3. **GBM**: XGBoost/LightGBM por target. Default productivo.
4. **Jerárquico bayesiano** (PyMC): efectos parcialmente pooled por jugador / equipo / rival. Mejor con poca data por entidad.
5. **Neural con embeddings**: player_id y team_id como embeddings denses. Útil con MUCHA data.

## Métricas

- MAE (escala interpretable)
- RMSE (penaliza errores grandes)
- Calibración (cuando predice "2 shots", ¿el promedio observado es 2?)
- Log-likelihood si el modelo es probabilístico (jerárquico bayesiano)
- Comparación contra el baseline (% mejora)

## Estado actual

### Smoke tests
- `shots_baseline.py`: rolling avg vence naive 14% (MAE 0.815 vs 0.944). Demuestra que hay señal predictiva en la historia reciente.

### Modelos XGBoost (primera tanda)
- `xgb_predictor.py`: framework genérico que entrena cualquier target sobre `statsbomb_player_match.parquet`. Features compartidas (rolling 3/5/10, career mean, days_rest, minutes, is_home).
- **10 targets entrenados** sobre 22,597 filas (train 15,836 / test 6,761, cutoff temporal 2022-01-23). Ver `reports/SUMMARY.md` para tabla comparativa completa.
- Top mejora: **passes_completed +24.68% vs baseline rolling 5**.
- Targets sparse (shots_on_target, dribbles_completed) no mejoran vs baseline → necesitan modelos por posición o conteos explícitos (Poisson).

### Reportes por target
Cada entrenamiento escribe `reports/<target>_xgb.md` con: MAE/RMSE modelo y baseline, importancia de features, tabla de calibración 10-bins.

## Cómo correr

```powershell
# entrenar un target:
python 08_models\xgb_predictor.py --target passes_completed

# entrenar varios:
python 08_models\xgb_predictor.py --targets shots,passes_completed,xg,tackles

# targets válidos:
# shots, shots_on_target, goals, assists, passes_attempted, passes_completed,
# key_passes, xg, dribbles_attempted, dribbles_completed, tackles,
# interceptions, fouls_committed, fouls_drawn
```

## Próximos pasos

Ver `reports/SUMMARY.md` sección "Próximos pasos sugeridos".
