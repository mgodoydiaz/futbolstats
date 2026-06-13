r"""Parser del JSON de cuotas de Betano → estructuras normalizadas.

Betano (lat.betano.com) está detrás de DataDome (bot-detection), así que no se
puede scrapear con ``requests`` directo. El JSON se extrae en el navegador
(sesión ya logueada / pasado el captcha) con un snippet JS sobre el DOM, o vía
el Chrome MCP — ver ``06_ingestion/betano_extract.md``. Este módulo sólo
**parsea** ese JSON; no toca la red.

Convierte cada mercado a una forma uniforme:

    over_under(market)  → {line: {"over": odds, "under": odds}}
    one_x_two()         → {"home": o, "draw": o, "away": o}
    yes_no(market)      → {"yes": o, "no": o}
    player_shots()      → {player_name: {1: o, 2: o, ...}}  (umbrales acumulados N+)
    player_goalscorer() → {player_name: {"anytime": o, "first": o, "last": o}}
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _line_from(sel: str) -> float | None:
    m = re.search(r"(\d+\.?\d*)", sel)
    return float(m.group(1)) if m else None


def over_under(market: dict) -> dict[float, dict]:
    """Mercado Más/Menos → {linea: {'over': cuota, 'under': cuota}}."""
    out: dict[float, dict] = {}
    rows = []
    for key in ("principal", "alternativas", "cuotas"):
        rows.extend(market.get(key, []))
    for r in rows:
        sel = r.get("seleccion", "")
        line = _line_from(sel)
        if line is None:
            continue
        side = "over" if ("Más" in sel or "Mas" in sel or "Over" in sel) else "under"
        out.setdefault(line, {})[side] = r["cuota"]
    return out


def one_x_two(market: dict) -> dict:
    """Mercado 1X2 → {'home': c, 'draw': c, 'away': c} (1=primer equipo)."""
    out = {}
    for r in market.get("cuotas", []):
        sel = r["seleccion"].lower()
        if sel.startswith("1") or "(catar" in sel or "(local" in sel:
            out["home"] = r["cuota"]
        elif sel.startswith("x") or "empate" in sel:
            out["draw"] = r["cuota"]
        elif sel.startswith("2") or "(suiza" in sel or "(visita" in sel:
            out["away"] = r["cuota"]
    return out


def yes_no(market: dict) -> dict:
    out = {}
    for r in market.get("cuotas", []):
        sel = r["seleccion"].lower()
        if sel.startswith("sí") or sel.startswith("si"):
            out["yes"] = r["cuota"]
        elif sel.startswith("no"):
            out["no"] = r["cuota"]
    return out


def correct_scores(market: dict) -> dict[tuple[int, int], float]:
    out = {}
    for r in market.get("cuotas", []):
        m = re.match(r"(\d+)\s*-\s*(\d+)", r["seleccion"])
        if m:
            out[(int(m.group(1)), int(m.group(2)))] = r["cuota"]
    return out


def player_shots(market: dict) -> dict[str, dict[int, float]]:
    """Tiros al arco por jugador → {jugador: {1: c, 2: c, ...}} (umbrales N+)."""
    out = {}
    for team, players in market.get("jugadores", {}).items():
        for p in players:
            thresholds = {}
            for k, v in p.get("cuotas", {}).items():
                m = re.match(r"(\d+)", k)
                if m:
                    thresholds[int(m.group(1))] = v
            out[p["jugador"]] = thresholds
    return out


def player_goalscorer(market: dict) -> dict[str, dict]:
    """Goleador por jugador → {jugador: {'anytime': c, 'first': c, 'last': c}}."""
    out = {}
    for team, players in market.get("jugadores", {}).items():
        for p in players:
            out[p["jugador"]] = {
                "anytime": p.get("cualquier_momento"),
                "first": p.get("primero"),
                "last": p.get("ultimo"),
            }
    return out


def teams_from_meta(data: dict) -> tuple[str, str]:
    """'Catar vs Suiza' → ('Catar', 'Suiza')."""
    parts = re.split(r"\s+vs\.?\s+", data.get("partido", ""), flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return "", ""
