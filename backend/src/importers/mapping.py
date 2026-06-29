"""Generic CSV column-mapping import — the fallback when no parser recognizes a file.

When ``detect_format`` finds nothing but the upload is a CSV, the user maps each scryme field to one
of the file's columns; ``parse_with_mapping`` then turns the rows into :class:`ImportRow`s. The
fields and a best-effort auto-guess live here so the wizard route stays thin.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from src.importers.base import ImportRow
from src.importers.util import normalize_finish, normalize_language, to_float, to_int


@dataclass
class MapField:
    key: str
    label: str
    required: bool = False
    # Lowercase header substrings used to auto-guess the column (first match wins).
    hints: tuple[str, ...] = ()


MAP_FIELDS: list[MapField] = [
    MapField("name", "Card name", required=True, hints=("name",)),
    MapField("quantity", "Quantity", hints=("quantity", "qty", "count")),
    MapField("set_code", "Set code", hints=("set code", "edition code", "set", "edition")),
    MapField("collector_number", "Collector number",
             hints=("collector", "card number", "number")),
    MapField("scryfall_id", "Scryfall ID", hints=("scryfall",)),
    MapField("finish", "Finish / foil", hints=("finish", "foil", "printing")),
    MapField("condition", "Condition", hints=("condition",)),
    MapField("language", "Language", hints=("language", "lang")),
    MapField("purchase_price", "Purchase price",
             hints=("purchase price", "price bought", "my price", "price")),
]


def csv_headers(text: str) -> list[str] | None:
    """The header row if *text* parses as a CSV with at least two columns and a data row."""
    sample = text.lstrip()
    if not sample:
        return None
    # Honor a leading ``sep=,`` hint (Dragon Shield style) so odd exports still map.
    lines = sample.splitlines()
    if lines and lines[0].strip().lower().startswith("sep="):
        sample = "\n".join(lines[1:])
    reader = csv.reader(io.StringIO(sample))
    try:
        header = next(reader)
        has_data = next(reader, None) is not None
    except StopIteration:
        return None
    header = [h.strip() for h in header if h.strip()]
    if len(header) < 2 or not has_data:
        return None
    return header


def guess_mapping(headers: list[str]) -> dict[str, str]:
    """Best-effort {field_key: header} guess by matching each field's hints against the headers."""
    lowered = [(h, h.lower()) for h in headers]
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for field in MAP_FIELDS:
        for hint in field.hints:
            match = next((h for h, low in lowered if hint in low and h not in used), None)
            if match:
                mapping[field.key] = match
                used.add(match)
                break
    return mapping


def parse_with_mapping(text: str, mapping: dict[str, str]) -> list[ImportRow]:
    """Parse *text* into ImportRows using a {field_key: column_name} mapping.

    Only ``name`` is required; unmapped fields fall back to ImportRow defaults.
    """
    name_col = mapping.get("name")
    if not name_col:
        return []
    sample = text.lstrip()
    lines = sample.splitlines()
    if lines and lines[0].strip().lower().startswith("sep="):
        sample = "\n".join(lines[1:])

    reader = csv.DictReader(io.StringIO(sample))
    rows: list[ImportRow] = []

    def cell(raw: dict, key: str) -> str | None:
        col = mapping.get(key)
        return (raw.get(col) or "").strip() if col else None

    for raw in reader:
        name = (raw.get(name_col) or "").strip()
        if not name:
            continue
        set_code = cell(raw, "set_code")
        rows.append(
            ImportRow(
                name=name,
                quantity=to_int(cell(raw, "quantity")),
                set_code=set_code.lower() if set_code else None,
                collector_number=cell(raw, "collector_number") or None,
                scryfall_id=cell(raw, "scryfall_id") or None,
                finish=normalize_finish(cell(raw, "finish")),
                condition=cell(raw, "condition") or None,
                language=normalize_language(cell(raw, "language")),
                purchase_price=to_float(cell(raw, "purchase_price")),
            )
        )
    return rows
