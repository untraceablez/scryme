"""Delver Lens parser + detection + matching tests."""

from pathlib import Path

import pytest
from src.importers.base import detect_format
from src.importers.delver import DelverImporter
from src.importers.matching import match_rows

from tests.seed_cards import seed_cards

FIXTURES = Path(__file__).parent / "fixtures"
DELVER_CSV = (FIXTURES / "delver_sample.csv").read_text()
MB_CSV = (FIXTURES / "manabox_sample.csv").read_text()


def test_detect_delver():
    assert detect_format(DELVER_CSV) is DelverImporter
    # ManaBox also has a Scryfall ID column but must not be claimed by Delver.
    assert detect_format(MB_CSV) is not DelverImporter


def test_parse_case_insensitive_columns():
    rows = DelverImporter.parse(DELVER_CSV)
    assert len(rows) == 2

    lotus = rows[0]
    assert lotus.name == "Black Lotus"
    assert lotus.scryfall_id == "00000000-0000-0000-0000-0000000000b1"
    assert lotus.finish == "normal"  # blank Foil column
    assert lotus.language == "en"

    bolt = rows[1]
    assert bolt.finish == "foil"
    assert bolt.quantity == 3


@pytest.mark.asyncio
async def test_match_by_scryfall_id(session):
    await seed_cards(session)
    rows = DelverImporter.parse(DELVER_CSV)
    matched = await match_rows(session, rows)
    assert all(m.method == "scryfall_id" for m in matched)
