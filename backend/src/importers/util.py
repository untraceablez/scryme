"""Shared helpers for CSV importers."""

from __future__ import annotations

_LANGUAGES = {
    "english": "en", "en": "en",
    "japanese": "ja", "ja": "ja",
    "german": "de", "de": "de",
    "french": "fr", "fr": "fr",
    "italian": "it", "it": "it",
    "spanish": "es", "es": "es",
    "portuguese": "pt", "pt": "pt",
    "russian": "ru", "ru": "ru",
    "korean": "ko", "ko": "ko",
    "chinese simplified": "zhs", "chinese traditional": "zht", "chinese": "zhs",
}


def to_int(value: str | None, default: int = 1) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def to_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def normalize_language(value: str | None) -> str:
    v = (value or "en").strip().lower()
    if v in _LANGUAGES:
        return _LANGUAGES[v]
    return v[:2] if len(v) >= 2 else "en"


def normalize_finish(value: str | None) -> str:
    """Map a foil/printing column to normal | foil | etched."""
    v = (value or "").strip().lower()
    if v in ("foil", "etched"):
        return v
    if v in ("normal", "nonfoil", "non-foil", "", "false", "no"):
        return "normal"
    if v in ("true", "yes"):  # Deckbox-style boolean foil column
        return "foil"
    return "normal"
