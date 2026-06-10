r"""Estimación de tasas de eventos raros por jugador (goles, tarjetas).

Predecir ``P(jugador marca)`` o ``P(jugador es amonestado)`` para un partido se
reduce a estimar una **tasa** $\lambda$ (eventos esperados en ese partido) y luego
aplicar la distribución de conteo (``lib.betting.poisson_over_under``).

El problema central es que en torneos cada jugador tiene **pocos partidos**: la
tasa cruda goles/partido es ruidosísima (un delantero con 2 goles en 3 partidos
no marca al 67 %). Por eso ofrecemos varios métodos, **seleccionables por
parámetro**, de menos a más honestos:

    method="rate"          goles / partidos. Cruda, ignora minutos. Baseline naive.
    method="per90"         goles por 90' × (minutos_esperados/90). Ajusta minutos.
    method="shrinkage"     per90 con encogimiento empírico-Bayes hacia la media de
                           la posición (Gamma-Poisson conjugado). El recomendado.
    method="xg_shrinkage"  igual que shrinkage pero sobre xG en vez de goles —
                           xG es menos ruidoso, mejor estimador de la tasa real.

Todos devuelven, por jugador, ``lam_per90`` (tasa) y ``lam_match`` (eventos
esperados en un partido dado ``expected_minutes``). El ajuste por rival es un
``hook`` opcional (multiplicador), porque en un Mundial mapear selecciones a
ratings de club (ClubElo) no es directo — ver ``opponent_multiplier``.

Uso típico:
    from lib.scoring import estimate_rate, prob_at_least_one
    rates = estimate_rate(history, target_col="goals", method="shrinkage")
    p_score = prob_at_least_one(rates["lam_match"])
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

# Métodos disponibles (se rellena con @_register más abajo).
METHODS: dict[str, Callable] = {}


def _register(name: str):
    def deco(fn):
        METHODS[name] = fn
        return fn
    return deco


# --------------------------------------------------------------------------
# Agregación de historial por jugador
# --------------------------------------------------------------------------

def aggregate_history(
    history: pd.DataFrame,
    target_col: str,
    minutes_col: str = "minutes_played",
    group_col: str = "position_group",
    xg_col: str | None = "xg",
    id_cols: tuple[str, str] = ("player_id", "player_name"),
) -> pd.DataFrame:
    """Colapsa el historial partido-a-partido a totales por jugador.

    Devuelve por jugador: partidos, suma del target, minutos totales, exposición
    en unidades de 90', grupo de posición (la moda) y suma de xG si está.
    """
    pid, pname = id_cols
    g = history.groupby(pid)
    out = pd.DataFrame({
        "matches": g.size(),
        "events": g[target_col].sum(),
        "minutes": g[minutes_col].sum() if minutes_col in history else g.size() * 90,
    })
    out["exposure90"] = out["minutes"] / 90.0
    if pname in history.columns:
        out[pname] = g[pname].first()
    if group_col in history.columns:
        out[group_col] = g[group_col].agg(lambda s: s.mode().iloc[0] if len(s.mode()) else None)
    if xg_col and xg_col in history.columns:
        out["xg_sum"] = g[xg_col].sum()
    return out.reset_index()


def positional_rate(agg: pd.DataFrame, group_col: str = "position_group",
                    events_col: str = "events") -> pd.Series:
    """Tasa per-90 media de cada grupo de posición (pooled). Sirve de prior."""
    grp = agg.groupby(group_col).apply(
        lambda d: d[events_col].sum() / max(d["exposure90"].sum(), 1e-9),
        include_groups=False,
    )
    return grp


# --------------------------------------------------------------------------
# Métodos de estimación (todos firman (agg, **kw) -> agg con lam_per90)
# --------------------------------------------------------------------------

@_register("rate")
def _rate(agg: pd.DataFrame, **kw) -> pd.DataFrame:
    """goles/partido crudo. Convertido a per90 dividiendo por (min medio/90)."""
    agg = agg.copy()
    per_match = agg["events"] / agg["matches"].clip(lower=1)
    min_per_match = (agg["minutes"] / agg["matches"].clip(lower=1)).clip(lower=1)
    agg["lam_per90"] = per_match / (min_per_match / 90.0)
    return agg


@_register("per90")
def _per90(agg: pd.DataFrame, **kw) -> pd.DataFrame:
    """Tasa per-90 directa, sin encoger. Inestable con poca exposición."""
    agg = agg.copy()
    agg["lam_per90"] = agg["events"] / agg["exposure90"].clip(lower=1e-9)
    return agg


def _shrink(agg: pd.DataFrame, events_col: str, group_col: str,
            prior_strength: float) -> pd.DataFrame:
    """Encogimiento Gamma-Poisson conjugado hacia la media de la posición.

        lam = (eventos + m_grupo · c) / (exposición90 + c)

    ``c`` = fuerza del prior en unidades de 90' (pseudo-exposición). Jugadores con
    poca exposición se acercan a ``m_grupo``; con mucha, a su tasa propia.
    """
    agg = agg.copy()
    m_group = positional_rate(agg, group_col=group_col, events_col=events_col)
    global_m = agg[events_col].sum() / max(agg["exposure90"].sum(), 1e-9)
    if group_col in agg.columns:
        prior = agg[group_col].map(m_group).fillna(global_m)
    else:
        prior = pd.Series(global_m, index=agg.index)
    c = float(prior_strength)
    agg["lam_per90"] = (agg[events_col] + prior * c) / (agg["exposure90"] + c)
    return agg


@_register("shrinkage")
def _shrinkage(agg: pd.DataFrame, group_col: str = "position_group",
               prior_strength: float = 4.0, **kw) -> pd.DataFrame:
    return _shrink(agg, "events", group_col, prior_strength)


@_register("xg_shrinkage")
def _xg_shrinkage(agg: pd.DataFrame, group_col: str = "position_group",
                  prior_strength: float = 4.0, **kw) -> pd.DataFrame:
    if "xg_sum" not in agg.columns:
        raise KeyError("xg_shrinkage requiere columna xg en el historial "
                       "(pasá xg_col a aggregate_history).")
    return _shrink(agg, "xg_sum", group_col, prior_strength)


# --------------------------------------------------------------------------
# API principal
# --------------------------------------------------------------------------

def estimate_rate(
    history: pd.DataFrame,
    target_col: str = "goals",
    method: str = "shrinkage",
    minutes_col: str = "minutes_played",
    group_col: str = "position_group",
    xg_col: str | None = "xg",
    prior_strength: float = 4.0,
    expected_minutes: float = 90.0,
    min_matches: int = 1,
) -> pd.DataFrame:
    """Estima λ por jugador con el método elegido.

    Parameters
    ----------
    history : partido-a-partido (una fila por jugador-partido).
    target_col : columna a modelar (``"goals"``, ``"yellow_total"``, ...).
    method : una clave de :data:`METHODS`.
    expected_minutes : minutos que se espera juegue en el partido a predecir
        (90 = titular completo). ``lam_match = lam_per90 · expected_minutes/90``.
    prior_strength : fuerza del encogimiento (sólo métodos shrinkage).

    Returns
    -------
    DataFrame con ``[player_id, (player_name), matches, lam_per90, lam_match]``.
    """
    if method not in METHODS:
        raise ValueError(f"método desconocido: {method!r}. Opciones: {sorted(METHODS)}")
    agg = aggregate_history(history, target_col, minutes_col, group_col, xg_col)
    agg = agg[agg["matches"] >= min_matches].copy()
    agg = METHODS[method](agg, group_col=group_col, prior_strength=prior_strength)
    agg["lam_match"] = agg["lam_per90"] * (expected_minutes / 90.0)
    agg["method"] = method
    return agg


def prob_at_least_one(lam: pd.Series | np.ndarray | float):
    """``P(Y >= 1)`` bajo Poisson(λ) = ``1 - e^{-λ}``. Para mercados over 0.5."""
    lam = np.asarray(lam, dtype=float)
    return 1.0 - np.exp(-np.clip(lam, 0.0, None))


def opponent_multiplier(
    opp_strength: pd.Series | np.ndarray,
    baseline: float,
    elasticity: float = 1.0,
) -> np.ndarray:
    """Multiplicador opcional de λ por fuerza defensiva del rival.

    ``mult = (baseline / opp_strength) ** elasticity``. Rival más fuerte que la
    media (``opp_strength > baseline``) baja λ; más débil, la sube. ``baseline``
    es la fuerza promedio de referencia. Devuelve 1.0 donde falta el dato.
    """
    s = np.asarray(opp_strength, dtype=float)
    mult = np.where(s > 0, (baseline / s) ** elasticity, 1.0)
    return np.where(np.isfinite(mult), mult, 1.0)
