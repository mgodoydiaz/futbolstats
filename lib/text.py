"""Text normalization for cross-source name matching.

Different data sources spell player/team names slightly differently:
    Müller vs Muller, Mbappé vs Mbappe, AS Roma vs Roma, etc.

`normalize_name` produces a canonical form for joining.
"""
from __future__ import annotations

import re

from unidecode import unidecode


_PUNCT = re.compile(r"[^\w\s-]")
_WHITESPACE = re.compile(r"\s+")
_TEAM_PREFIXES = re.compile(
    r"^(fc|cf|sc|as|ac|us|ss|cd|sd|ca|ra|ud|rcd|rcde|cl|ssc|afc|sv|tsg|bsc|borussia)\s+",
    re.IGNORECASE,
)
_TEAM_SUFFIXES = re.compile(
    r"\s+(fc|cf|sc|sad|sa|cp|football club|de futbol|calcio)$",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    """Canonical form for matching across sources.

    Lowercases, strips accents, collapses whitespace, drops punctuation
    (keeps hyphens, useful for surnames like "Saint-Maximin").
    """
    if not isinstance(name, str):
        return ""
    s = unidecode(name).lower().strip()
    s = _PUNCT.sub(" ", s)
    s = _WHITESPACE.sub(" ", s)
    return s.strip()


def normalize_team_name(name: str) -> str:
    """Like `normalize_name` but also strips common club prefixes/suffixes.

    "FC Barcelona" → "barcelona", "AS Roma" → "roma", "Real Madrid CF" → "real madrid"
    Not bulletproof — some clubs (Manchester United) have no prefix.
    """
    s = normalize_name(name)
    s = _TEAM_PREFIXES.sub("", s)
    s = _TEAM_SUFFIXES.sub("", s)
    return s.strip()
