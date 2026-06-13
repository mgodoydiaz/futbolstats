r"""Modelo de partido a nivel equipo — goles esperados → mercados derivados.

A partir del historial estima los **goles esperados** de cada equipo y construye
una matriz de marcador con Poisson independiente. De esa matriz salen casi todos
los mercados de partido que cotiza una casa:

    1X2 (local/empate/visita)      P(over/under total)      ambos anotan (BTTS)
    marcador correcto              goles por equipo over/under

Supuestos (y sus límites):
- **Poisson independiente** por equipo: ignora la correlación entre goles de
  ambos (los partidos goleados/cerrados se contagian). Dixon-Coles lo corrige;
  acá no se aplica para no sobre-ajustar con muestras chicas de selección.
- **Goles esperados** = mezcla de ataque propio y defensa rival, encogidos hacia
  la media global (las selecciones con pocos partidos tiran a la media).
- Sin ventaja de localía (Mundial en cancha neutral). Pasá ``home_adv`` si querés.

Corners y tarjetas usan sus propias tablas (set-pieces / discipline), no la
matriz de goles — ver :func:`expected_corners` y :func:`expected_cards`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import poisson


# --------------------------------------------------------------------------
# Fuerzas de equipo (goles a favor / en contra) con encogimiento
# --------------------------------------------------------------------------

def team_strengths(player_match: pd.DataFrame, prior_strength: float = 5.0) -> pd.DataFrame:
    """Goles/partido a favor y en contra por equipo, encogidos a la media global.

    Devuelve ``[team, n, gf, ga]`` donde ``gf``/``ga`` ya están regularizados:
    un equipo con pocos partidos tira hacia el promedio del torneo.
    """
    # goles por (match, team) y total del match → conceded = total - propios.
    by_mt = player_match.groupby(["match_id", "team_name"], as_index=False)["goals"].sum()
    total = by_mt.groupby("match_id")["goals"].sum().rename("match_total")
    by_mt = by_mt.join(total, on="match_id")
    by_mt["conceded"] = by_mt["match_total"] - by_mt["goals"]

    agg = by_mt.groupby("team_name").agg(
        n=("goals", "size"), gf_raw=("goals", "mean"), ga_raw=("conceded", "mean"))
    global_gf = by_mt["goals"].mean()
    global_ga = by_mt["conceded"].mean()
    c = prior_strength
    agg["gf"] = (agg["gf_raw"] * agg["n"] + global_gf * c) / (agg["n"] + c)
    agg["ga"] = (agg["ga_raw"] * agg["n"] + global_ga * c) / (agg["n"] + c)
    agg["global_gf"] = global_gf
    return agg.reset_index()


def expected_goals(strengths: pd.DataFrame, team_a: str, team_b: str,
                   home_adv: float = 0.0) -> tuple[float, float]:
    """Goles esperados (λ) de cada equipo = mezcla ataque propio × defensa rival.

    Normaliza por la media global para que ``λ_a`` escale con lo flojo/fuerte que
    sea la defensa de B respecto al promedio. ``home_adv`` (p.ej. 0.2) suma a λ del
    primer equipo si jugara de local; 0 para cancha neutral.
    """
    s = strengths.set_index("team_name")
    g = float(s["global_gf"].iloc[0])
    a, b = s.loc[team_a], s.loc[team_b]
    lam_a = (a["gf"] / g) * (b["ga"] / g) * g + home_adv
    lam_b = (b["gf"] / g) * (a["ga"] / g) * g
    return max(lam_a, 1e-3), max(lam_b, 1e-3)


# --------------------------------------------------------------------------
# Matriz de marcador y mercados derivados
# --------------------------------------------------------------------------

def scoreline_matrix(lam_a: float, lam_b: float, max_goals: int = 10) -> np.ndarray:
    """Matriz ``P[i, j]`` = P(A marca i, B marca j) bajo Poisson independiente."""
    pa = poisson.pmf(np.arange(max_goals + 1), lam_a)
    pb = poisson.pmf(np.arange(max_goals + 1), lam_b)
    m = np.outer(pa, pb)
    return m / m.sum()  # renormaliza la cola truncada


def markets_from_matrix(m: np.ndarray) -> dict:
    """Deriva 1X2, BTTS y over/under de goles totales de la matriz de marcador."""
    n = m.shape[0]
    idx = np.arange(n)
    home = float(np.tril(m, -1).sum())          # A > B
    away = float(np.triu(m, 1).sum())           # B > A
    draw = float(np.trace(m))
    btts = float(m[1:, 1:].sum())               # ambos >= 1
    totals = {}
    tot_goals = idx[:, None] + idx[None, :]
    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        over = float(m[tot_goals > line].sum())
        totals[line] = {"over": over, "under": 1 - over}
    return {"home": home, "draw": draw, "away": away, "btts_yes": btts,
            "btts_no": 1 - btts, "totals": totals}


def team_total_goals(lam: float, line: float) -> dict:
    """Over/under de goles de UN equipo (Poisson marginal)."""
    over = float(1 - poisson.cdf(np.floor(line), lam))
    return {"over": over, "under": 1 - over}


def correct_score(m: np.ndarray, a: int, b: int) -> float:
    """P(marcador exacto a-b) si entra en la matriz."""
    if a < m.shape[0] and b < m.shape[1]:
        return float(m[a, b])
    return 0.0


# --------------------------------------------------------------------------
# Corners y tarjetas (tablas propias, no la matriz de goles)
# --------------------------------------------------------------------------

def expected_corners(setpieces: pd.DataFrame, team_a: str, team_b: str) -> tuple[float, float, float]:
    """Corners esperados (a_for, b_for, total) mezclando a-favor y rival-en-contra."""
    def rates(name):
        s = setpieces[setpieces["team"] == name]
        if len(s) == 0:
            return None, None
        return s["corners"].mean(), s["corners_against"].mean()
    af, _ = rates(team_a)
    bf, ba = rates(team_b)
    _, aa = rates(team_a)
    if af is None or bf is None:
        return np.nan, np.nan, np.nan
    a_exp = (af + ba) / 2.0
    b_exp = (bf + aa) / 2.0
    return a_exp, b_exp, a_exp + b_exp


def expected_cards(player_match: pd.DataFrame, discipline: pd.DataFrame,
                   team_a: str, team_b: str) -> tuple[float, float, float]:
    """Tarjetas amarillas esperadas por equipo y total (de la tabla discipline)."""
    d = discipline.copy()
    d["pid_num"] = d["player_id"].astype("float64")
    d["mid_num"] = d["match_id"].astype("float64")
    mpx = player_match.copy()
    mpx["pid_num"] = mpx["player_id_sb"].astype("float64")
    mpx["mid_num"] = mpx["match_id"].str.replace("sb_", "", regex=False).astype("float64")
    j = mpx[["pid_num", "mid_num", "team_name", "match_id"]].merge(
        d[["pid_num", "mid_num", "yellow_total"]], on=["pid_num", "mid_num"], how="left")
    j["yellow_total"] = j["yellow_total"].fillna(0)

    def rate(name):
        tmc = j[j["team_name"] == name].groupby("match_id")["yellow_total"].sum()
        return float(tmc.mean()) if len(tmc) else np.nan
    a_exp, b_exp = rate(team_a), rate(team_b)
    total = (a_exp if a_exp == a_exp else 0) + (b_exp if b_exp == b_exp else 0)
    return a_exp, b_exp, total
