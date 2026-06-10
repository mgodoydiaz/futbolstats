# StatsBomb player-match correlation report

Source: `02_data_processed\events_clean\statsbomb_player_match.parquet`
Rows: 26,295
Players: 3,698
Matches: 908

## Per-match means and dispersion

| Stat | mean | median | std | p90 |
|------|-----:|-------:|----:|----:|
| minutes_played | 72.99 | 93 | 30.41 | 96.0 |
| goals | 0.10 | 0 | 0.34 | 0.0 |
| assists | 0.06 | 0 | 0.25 | 0.0 |
| shots | 0.89 | 0 | 1.30 | 3.0 |
| shots_on_target | 0.30 | 0 | 0.65 | 1.0 |
| xg | 0.10 | 0 | 0.22 | 0.3 |
| passes_attempted | 33.46 | 30 | 22.87 | 64.0 |
| passes_completed | 26.12 | 21 | 20.26 | 54.0 |
| key_passes | 0.62 | 0 | 1.02 | 2.0 |
| dribbles_attempted | 1.15 | 1 | 1.70 | 3.0 |
| dribbles_completed | 0.66 | 0 | 1.13 | 2.0 |
| tackles | 1.29 | 1 | 1.54 | 3.0 |
| interceptions | 0.81 | 0 | 1.21 | 2.0 |
| fouls_committed | 0.90 | 1 | 1.11 | 2.0 |
| fouls_drawn | 0.86 | 0 | 1.15 | 2.0 |

## Top 15 correlated stat pairs

| Stat A | Stat B | Pearson r |
|--------|--------|----------:|
| passes_attempted | passes_completed | +0.977 |
| dribbles_attempted | dribbles_completed | +0.869 |
| shots | shots_on_target | +0.713 |
| shots | xg | +0.689 |
| shots_on_target | xg | +0.661 |
| minutes_played | passes_attempted | +0.656 |
| goals | shots_on_target | +0.626 |
| goals | xg | +0.625 |
| minutes_played | passes_completed | +0.584 |
| goals | shots | +0.434 |
| assists | key_passes | +0.377 |
| shots | dribbles_attempted | +0.359 |
| dribbles_attempted | fouls_drawn | +0.333 |
| passes_attempted | tackles | +0.329 |
| minutes_played | tackles | +0.325 |

## Player consistency in shots/match (top players, min 10 matches)

Most consistent (low coefficient of variation, mean_shots >= 2):

| Player | matches | mean | std | CV |
|--------|--------:|-----:|----:|---:|
| Antonio Perošević | 14 | 3.64 | 1.45 | 0.40 |
| Julie Beth Ertz | 10 | 2.10 | 0.88 | 0.42 |
| Federico Santiago Valverde Dipetta | 11 | 2.45 | 1.13 | 0.46 |
| Junior Stanislas | 21 | 2.19 | 1.03 | 0.47 |
| Hakim Ziyech | 10 | 2.00 | 0.94 | 0.47 |
| Cristiano Ronaldo dos Santos Aveiro | 18 | 4.06 | 1.95 | 0.48 |
| Cleiton Augusto Oliveira Silva | 19 | 2.58 | 1.30 | 0.51 |
| Harry Kane | 63 | 3.49 | 1.82 | 0.52 |
| Álvaro Vázquez García | 23 | 3.13 | 1.66 | 0.53 |
| Suhair Vadakkepeedika | 19 | 2.42 | 1.30 | 0.54 |

Most variable (high CV, mean_shots >= 2):

| Player | matches | mean | std | CV |
|--------|--------:|-----:|----:|---:|
| Lieke Martens | 12 | 2.50 | 3.26 | 1.30 |
| Wilfried Guemiand Bony | 26 | 2.35 | 2.48 | 1.06 |
| Toni Kroos | 14 | 2.00 | 2.00 | 1.00 |
| Caitlin Jade Foord | 11 | 2.09 | 2.07 | 0.99 |
| Jamal Musiala | 10 | 2.10 | 2.08 | 0.99 |
| Lindsey Michelle Horan | 10 | 2.30 | 2.21 | 0.96 |
| Christian Benteke Liolo | 30 | 2.13 | 2.05 | 0.96 |
| Andy Carroll | 27 | 2.04 | 1.95 | 0.96 |
| Bamidele Alli | 38 | 2.08 | 1.98 | 0.95 |
| Mathias Coureur | 10 | 2.10 | 1.97 | 0.94 |