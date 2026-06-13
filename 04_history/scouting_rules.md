# Reglas de scouting — tendencias de equipos y jugadores

Heurísticas derivadas de los datos para interpretar pronósticos y detectar dónde
el modelo miente. Mezcla reglas **generales de modelado** con **tendencias
concretas** por equipo/jugador. Actualizar a medida que entren más datos.

> Las tendencias son del historial StatsBomb cargado (torneos). Si un equipo no
> jugó torneos recientes, su "tendencia" está **desactualizada** — ver fecha.

## Reglas generales de modelado (válidas siempre)

1. **Muestra chica = no confíes.** Jugador con < 5 partidos o equipo con < 6:
   el shrinkage los empuja a la media y el λ resultante es poco fiable. El filtro
   `--min-matches` existe para esto.
2. **El shrinkage sobre-corrige a los equipos débiles.** Una selección floja con
   pocos partidos (ej. Catar, 3 PJ) recibe goles esperados **inflados** hacia la
   media global. Si el mercado da a un equipo como víctima clara (cuota > 8 para
   ganar) y el modelo le da +EV alto, **es casi siempre error del modelo**, no valor.
3. **Datos de torneo = muchas tarjetas.** Mundiales/Euros tienen arbitraje
   estricto: ~2 amarillas por equipo/partido. El modelo de tarjetas tiende a
   predecir totales altos; comparар contra la línea con cuidado.
4. **Sin ajuste por rival.** El λ de un jugador es su promedio histórico, no
   ajustado a la defensa puntual de este rival. Bueno para rivales promedio,
   sesgado contra defensas extremas.
5. **Sin alineación confirmada.** Se asume que el jugador parte y juega sus
   minutos promedio. Un suplente sorpresa rompe el cálculo.
6. **Datos viejos ≠ forma actual.** El "momentum" del repo es del último torneo
   cargado, no de amistosos/eliminatorias recientes. No es forma real para 2026.

## Tendencias por equipo

### Suiza  _(datos: WC2022 + Euro2024, 18 PJ — confiable)_
- Ofensiva sólida: **1.94 goles/partido**, llega a octavos/cuartos seguido.
- **Corners ~5.8 a favor**, partidos de volumen medio-alto de corners.
- **~2 amarillas/partido** — disciplinada-media.
- Goleadores de referencia: **Embolo** (titular fijo, tira y marca), Amdouni,
  Okafor. Embolo es el ancla del ataque.

### Catar  _(datos: SÓLO WC2022, 3 PJ — NO confiable, desactualizado)_
- Anfitrión 2022 que perdió los 3 partidos: **0.33 goles/PJ, 2.33 en contra**.
- Pocos corners a favor (~3), defensa permeable.
- ⚠️ 3 partidos de hace 3.5 años. Cualquier predicción de Catar es casi un prior.

### Corea del Sur  _(datos: WC2022, 7 PJ)_
- Depende de **Son Heung-Min** para generación (3.3 tiros/PJ, el resto poco).
- Corners equilibrados (~5.6 a favor / 5.1 en contra).

### Chequia  _(datos: Euro2024, 8 PJ)_
- **Patrik Schick** es la vía de gol: 2.9 tiros, 1.6 al arco, 6 goles en 8 PJ.
  Es el jugador con mejor tasa de tiros al arco de los cubiertos.
- Concede muchos corners (6.75/PJ) — vulnerable a balón parado.

## Tendencias por jugador (de los cubiertos)

| Jugador | Equipo | tiros/PJ | SoT/PJ | regla |
|---------|--------|---------:|-------:|-------|
| Heung-Min Son | KOR | 3.3 | 0.9 | volumen alto de tiros, pocos al arco |
| Patrik Schick | CZE | 2.9 | 1.6 | máximo realizador, alta conversión a SoT |
| Breel Embolo | SUI | — | — | referencia ofensiva suiza, titular fijo |
| Gue-Sung Cho | KOR | 2.0 | 1.2 | revulsivo, buena tasa al arco en poca muestra |

## Cómo usar estas reglas

- Antes de creerle a un EV alto, pasá por la regla 2 y 3: ¿el valor viene de un
  equipo débil sobre-estimado o de un mercado de tarjetas inflado?
- Confiá más en: **props de jugadores con muchos PJ** (Son, Schick, Embolo) y en
  el **lado del favorito** (donde la muestra es buena).
- Desconfiá de: cualquier mercado dominado por el equipo de pocos partidos.
