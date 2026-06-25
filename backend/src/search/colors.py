"""Parse Scryfall color expressions into a set of WUBRG letters.

Accepts single letters (``w u b r g``), full names (``white`` ...), guild/shard/wedge names
(``azorius``, ``bant`` ...), and the special tokens ``c``/``colorless`` and ``m``/``multicolor``.
"""

from __future__ import annotations

LETTERS = {"w", "u", "b", "r", "g"}

_NAMES = {
    "white": "w", "blue": "u", "black": "b", "red": "r", "green": "g",
}

_COMBOS = {
    # Guilds
    "azorius": "wu", "dimir": "ub", "rakdos": "br", "gruul": "rg", "selesnya": "gw",
    "orzhov": "wb", "izzet": "ur", "golgari": "bg", "boros": "rw", "simic": "gu",
    # Shards
    "bant": "gwu", "esper": "wub", "grixis": "ubr", "jund": "brg", "naya": "rgw",
    # Wedges
    "abzan": "wbg", "jeskai": "urw", "sultai": "bgu", "mardu": "rwb", "temur": "gur",
    # Four/five color nicknames
    "chaos": "ubrg", "aggression": "wbrg", "altruism": "wurg", "growth": "wubg",
    "artifice": "wubr", "rainbow": "wubrg",
}


class ColorParseError(ValueError):
    pass


def parse_colors(value: str) -> tuple[set[str], str]:
    """Return (letters, special).

    special is "" for a normal letter set, "colorless" for c/colorless, or
    "multicolor" for m/multicolor (in which case letters is empty).
    """
    v = value.strip().lower()
    if v in ("c", "colorless"):
        return set(), "colorless"
    if v in ("m", "multicolor", "multicolored"):
        return set(), "multicolor"
    if v in _NAMES:
        return {_NAMES[v]}, ""
    if v in _COMBOS:
        return set(_COMBOS[v]), ""
    letters = set(v)
    if letters and letters <= LETTERS:
        return letters, ""
    raise ColorParseError(f"Unrecognized color expression “{value}”.")
