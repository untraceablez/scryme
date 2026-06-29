"""Collection import: format detection, parsers, card matching, and merge strategies.

A parser turns an uploaded export into normalized :class:`~src.importers.base.ImportRow` records;
matching resolves each row to a Scryfall card; the two-phase service stages a preview and then
applies a chosen :class:`~src.importers.merge.MergeStrategy`.
"""

# Importing the parser modules registers them in the format-detection registry. detect() rules
# are mutually exclusive, so registration order does not affect which parser claims a file.
from src.importers import (  # noqa: F401  (register parsers)
    archidekt,
    delver,
    dragonshield,
    manabox,
    moxfield,
)
from src.importers.base import ImportRow, detect_format
from src.importers.merge import MergeStrategy

__all__ = ["ImportRow", "MergeStrategy", "detect_format"]
