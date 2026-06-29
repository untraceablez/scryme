"""CSV column-mapping wizard: detection, guessing, parsing, and the two-step route."""

from pathlib import Path

import pytest
from src.importers.base import detect_format
from src.importers.mapping import csv_headers, guess_mapping, parse_with_mapping

FIXTURES = Path(__file__).parent / "fixtures"
GENERIC = (FIXTURES / "generic_sample.csv").read_text()


def test_generic_csv_is_not_auto_detected():
    assert detect_format(GENERIC) is None  # no known parser claims it
    assert csv_headers(GENERIC) == ["Quantity", "Card Name", "Set Code", "Card Number", "Foil"]


def test_csv_headers_rejects_non_csv():
    assert csv_headers("") is None
    assert csv_headers("just one column\nvalue") is None       # < 2 columns
    assert csv_headers("A,B,C") is None                        # header only, no data


def test_guess_mapping():
    guess = guess_mapping(["Quantity", "Card Name", "Set Code", "Card Number", "Foil"])
    assert guess["name"] == "Card Name"
    assert guess["quantity"] == "Quantity"
    assert guess["set_code"] == "Set Code"
    assert guess["collector_number"] == "Card Number"
    assert guess["finish"] == "Foil"


def test_parse_with_mapping():
    mapping = {"name": "Card Name", "quantity": "Quantity", "set_code": "Set Code",
               "collector_number": "Card Number", "finish": "Foil"}
    rows = parse_with_mapping(GENERIC, mapping)
    assert [r.name for r in rows] == ["Black Lotus", "Lightning Bolt"]
    assert rows[0].set_code == "lea" and rows[0].quantity == 1
    assert rows[1].finish == "foil" and rows[1].quantity == 2  # "Yes" -> foil


def test_parse_with_mapping_needs_name():
    assert parse_with_mapping(GENERIC, {"quantity": "Quantity"}) == []


@pytest.mark.asyncio
async def test_wizard_route_flow(client, session):
    # Unknown CSV -> the mapping wizard (not an error).
    files = {"file": ("cards.csv", GENERIC, "text/csv")}
    wiz = await client.post("/upload", files=files)
    assert wiz.status_code == 200
    assert "Map your columns" in wiz.text
    assert 'name="map_name"' in wiz.text

    # Submit the mapping -> the normal preview.
    data = {
        "csv": GENERIC,
        "map_name": "Card Name", "map_quantity": "Quantity", "map_set_code": "Set Code",
        "map_collector_number": "Card Number", "map_finish": "Foil",
    }
    preview = await client.post("/upload/mapped", data=data)
    assert preview.status_code == 200
    assert "2" in preview.text  # 2 rows parsed
