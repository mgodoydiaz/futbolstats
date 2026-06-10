r"""Scrape player-prop odds from Pinnacle via the public Arcadia JSON API.

Pinnacle's website is driven by a guest JSON API at
``guest.api.arcadia.pinnacle.com`` — no Selenium, no Cloudflare, just HTTP with
a long-lived guest ``X-API-Key``. We pull three things:

    /0.1/sports                         → sport ids (Soccer = 29)
    /0.1/sports/29/matchups             → every matchup (team games + "specials")
    /0.1/sports/29/markets/straight     → all prices in one bulk call

and join them into a long odds table compatible with the betting view's
``match_odds`` schema.

IMPORTANT — Pinnacle's soccer prop catalogue is small. Unlike Bet365 it does
**not** offer over/under shots / SoT / tackles / passes. For soccer players it
quotes only **goal** and **card** markets:

    anytime_goalscorer   "X To Score" / "Anytime Goalscorer"   → goals over 0.5
    first_goalscorer     "First Goalscorer"                    → pick-one (no O/U)
    to_score_or_assist   "X To Score Or Assist"                → over 0.5
    to_be_booked         "Player To Be Booked"                 → cards over 0.5

So the shots/tackles markets in ``build_matches_view`` are only fillable from a
book that quotes them; against Pinnacle, value analysis runs on goals & cards
(needs ``lam_goals`` / ``lam_cards`` columns — see the README follow-up).

Prices come as American odds; we store both the raw American price and the
decimal conversion (via :func:`lib.betting.american_to_decimal`).

Output:
    01_data_raw/odds/pinnacle_soccer_<YYYY-MM-DD>.parquet
    01_data_raw/_cache/pinnacle/                     (raw JSON, gitignored)

Usage:
    python 06_ingestion/pinnacle_scraper.py --list-leagues
    python 06_ingestion/pinnacle_scraper.py                       # all soccer props
    python 06_ingestion/pinnacle_scraper.py --league "Premier League"
    python 06_ingestion/pinnacle_scraper.py --dry-run             # parse, don't write

Disclaimer: for personal odds analysis. Respect Pinnacle's terms of use and
local law. This is not betting advice; wagering risks total loss of stake.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.betting import american_to_decimal  # noqa: E402
from lib.io import read_entities, write_parquet  # noqa: E402
from lib.text import normalize_name  # noqa: E402

CACHE_DIR = PROJECT_ROOT / "01_data_raw" / "_cache" / "pinnacle"
OUT_DIR = PROJECT_ROOT / "01_data_raw" / "odds"

API_BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
# Long-lived guest key the public website ships with. If Pinnacle rotates it the
# scraper will 401 — grab the current one from a browser devtools request header.
GUEST_API_KEY = "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R"
SOCCER_SPORT_ID = 29

HEADERS = {
    "X-API-Key": GUEST_API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://www.pinnacle.com/",
}

RATE_LIMIT_S = 1.0  # be polite between live calls

# description keyword → (canonical market, line, side). Goals & cards only.
MARKET_RULES = [
    ("to score or assist", ("to_score_or_assist", 0.5, "over")),
    ("anytime goalscorer", ("anytime_goalscorer", 0.5, "over")),
    ("to score",           ("anytime_goalscorer", 0.5, "over")),
    ("to be booked",       ("to_be_booked",       0.5, "over")),
    ("first goalscorer",   ("first_goalscorer",   float("nan"), "yes")),
    ("goal matchup",       ("goal_matchup",       float("nan"), "yes")),
]


# --------------------------------------------------------------------------
# HTTP with on-disk JSON cache
# --------------------------------------------------------------------------

def _get(path: str, cache_name: str | None = None, use_cache: bool = True) -> object:
    """GET ``API_BASE + path``; optionally cache the JSON under ``cache_name``."""
    cache_path = CACHE_DIR / f"{cache_name}.json" if cache_name else None
    if use_cache and cache_path and cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    req = urllib.request.Request(API_BASE + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(RATE_LIMIT_S)
    return data


# --------------------------------------------------------------------------
# Fetchers
# --------------------------------------------------------------------------

def fetch_matchups(use_cache: bool = True) -> list[dict]:
    stamp = date.today().isoformat()
    return _get(f"/sports/{SOCCER_SPORT_ID}/matchups",
                cache_name=f"matchups_{stamp}", use_cache=use_cache)


def fetch_markets(use_cache: bool = True) -> list[dict]:
    stamp = date.today().isoformat()
    return _get(f"/sports/{SOCCER_SPORT_ID}/markets/straight",
                cache_name=f"markets_{stamp}", use_cache=use_cache)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def classify_market(description: str) -> tuple[str, float, str] | None:
    """Map a special's description to (market, line, side). None if not a prop."""
    d = (description or "").lower()
    for needle, mapped in MARKET_RULES:
        if needle in d:
            return mapped
    return None


def _player_from_yesno_description(description: str) -> str:
    """'Harry Kane To Score' → 'Harry Kane'. Strips the trailing market phrase."""
    d = description
    for phrase in (" To Score Or Assist", " To Score", " To Be Booked",
                   " Anytime Goalscorer", " First Goalscorer"):
        if d.endswith(phrase):
            return d[: -len(phrase)].strip()
    return d.strip()


def build_player_index() -> dict[str, str]:
    """normalized player name → player_id, from the entities catalog."""
    try:
        players = read_entities("players")
    except FileNotFoundError:
        return {}
    idx: dict[str, str] = {}
    for _, row in players.iterrows():
        norm = row.get("name_normalized") or normalize_name(str(row.get("name", "")))
        if norm and norm not in idx:
            idx[norm] = str(row["player_id"])
    return idx


def parse_props(matchups: list[dict], markets: list[dict],
                league_filter: str | None = None) -> pd.DataFrame:
    """Join matchups + markets into a long odds table for player-prop specials."""
    # Index markets by matchupId.
    markets_by_matchup: dict[int, list[dict]] = {}
    for mk in markets:
        markets_by_matchup.setdefault(mk.get("matchupId"), []).append(mk)

    # Parent (team game) lookup: parentId → home/away/league/start.
    parents = {m["id"]: m for m in matchups if m.get("type") != "special"}

    player_idx = build_player_index()
    ts = datetime.now(timezone.utc).replace(tzinfo=None)
    rows: list[dict] = []

    for mu in matchups:
        if mu.get("type") != "special":
            continue
        special = mu.get("special") or {}
        if special.get("category") not in ("Player Props", "Player Goal Matchups"):
            continue
        mapped = classify_market(special.get("description", ""))
        if mapped is None:
            continue
        market, line, side = mapped

        league = (mu.get("league") or {}).get("name", "")
        if league_filter and league_filter.lower() not in league.lower():
            continue

        parent = parents.get(mu.get("parentId"), {})
        ppar = parent.get("participants", [])
        home = next((p["name"] for p in ppar if p.get("alignment") == "home"), None)
        away = next((p["name"] for p in ppar if p.get("alignment") == "away"), None)

        participants = mu.get("participants", [])
        pid2name = {p["id"]: p["name"] for p in participants}
        is_yesno = {p["name"].lower() for p in participants} == {"yes", "no"}

        mu_markets = markets_by_matchup.get(mu["id"], [])

        def _emit(player_name: str, american: float):
            try:
                dec = american_to_decimal(american)
            except (ValueError, TypeError):
                return
            norm = normalize_name(player_name)
            rows.append({
                "match_id": f"pinnacle_{mu.get('parentId')}",
                "pinnacle_matchup_id": mu["id"],
                "league": league,
                "start_time": mu.get("startTime"),
                "home_team": home,
                "away_team": away,
                "player_id": player_idx.get(norm, pd.NA),
                "player_name": player_name,
                "market": market,
                "line": line,
                "side": side,
                "bookmaker": "pinnacle",
                "price_american": american,
                "odds": round(dec, 4),
                "ts": ts,
            })

        if is_yesno:
            # Player named in the description; first price is the "Yes" side.
            player_name = _player_from_yesno_description(special.get("description", ""))
            for mk in mu_markets:
                prices = mk.get("prices", [])
                if prices:
                    _emit(player_name, prices[0].get("price"))
                break
        else:
            # One market, prices keyed by participantId = player.
            for mk in mu_markets:
                for pr in mk.get("prices", []):
                    pid = pr.get("participantId")
                    name = pid2name.get(pid)
                    if name and name.lower() != "no goalscorer":
                        _emit(name, pr.get("price"))

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scrape Pinnacle soccer player-prop odds (goals & cards)."
    )
    parser.add_argument("--league", default=None,
                        help="Substring filter on league name (e.g. 'Premier League').")
    parser.add_argument("--list-leagues", action="store_true",
                        help="Print leagues that currently have player props and exit.")
    parser.add_argument("--no-cache", action="store_true",
                        help="Force fresh API calls (ignore today's cached JSON).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and summarize, but don't write the parquet.")
    args = parser.parse_args()

    print("[pinnacle] fetching matchups + markets (Arcadia guest API)...")
    try:
        matchups = fetch_matchups(use_cache=not args.no_cache)
        markets = fetch_markets(use_cache=not args.no_cache)
    except Exception as e:  # noqa: BLE001
        print(f"[pinnacle] API call failed: {type(e).__name__}: {str(e)[:200]}")
        print("  If this is a 401/403, the guest API key may have rotated — refresh "
              "GUEST_API_KEY from a browser devtools request.")
        sys.exit(1)
    print(f"  matchups: {len(matchups):,} | markets: {len(markets):,}")

    df = parse_props(matchups, markets, league_filter=args.league)

    if args.list_leagues:
        if len(df) == 0:
            print("[pinnacle] no player props live right now.")
            return
        summary = (df.groupby("league")
                     .agg(props=("odds", "size"), players=("player_name", "nunique"))
                     .sort_values("props", ascending=False))
        print("\nLeagues with player props:")
        print(summary.to_string())
        return

    if len(df) == 0:
        print("[pinnacle] no player props matched. Pinnacle may not have any live, "
              "or your --league filter excluded them all.")
        return

    matched = int(df["player_id"].notna().sum())
    print(f"\n[pinnacle] parsed {len(df):,} prop quotes "
          f"({df['player_name'].nunique():,} players, "
          f"{matched:,} mapped to a known player_id)")
    print("  markets:", df["market"].value_counts().to_dict())
    print("\n  sample:")
    cols = ["league", "player_name", "market", "side", "price_american", "odds"]
    print(df[cols].head(8).to_string(index=False))

    if args.dry_run:
        print("\n[pinnacle] --dry-run: nothing written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"pinnacle_soccer_{date.today().isoformat()}.parquet"
    write_parquet(df, out)
    print(f"\n[pinnacle] wrote {len(df):,} rows -> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
