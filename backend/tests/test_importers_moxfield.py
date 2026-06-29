"""Moxfield + Archidekt parser and format-detection unit tests."""

from pathlib import Path

from src.importers.archidekt import ArchidektImporter
from src.importers.base import detect_format
from src.importers.moxfield import MoxfieldImporter

FIXTURES = Path(__file__).parent / "fixtures"
MOX = (FIXTURES / "moxfield_sample.csv").read_text()
ARCH = (FIXTURES / "archidekt_sample.csv").read_text()


def test_detect_moxfield():
    assert detect_format(MOX) is MoxfieldImporter


def test_detect_archidekt():
    assert detect_format(ARCH) is ArchidektImporter


def test_parse_moxfield():
    rows = MoxfieldImporter.parse(MOX)
    assert [r.name for r in rows] == ["Black Lotus", "Lightning Bolt", "Llanowar Elves"]
    assert rows[0].set_code == "lea"  # lowercased
    assert rows[0].collector_number == "232"
    assert rows[0].purchase_price == 5000.00
    assert rows[1].finish == "foil" and rows[1].quantity == 2
    assert rows[2].purchase_price is None  # blank


def test_parse_archidekt():
    rows = ArchidektImporter.parse(ARCH)
    assert rows[0].name == "Black Lotus"
    assert rows[0].set_code == "lea"
    assert rows[0].scryfall_id == "00000000-0000-0000-0000-0000000000b1"
    assert rows[1].finish == "foil" and rows[1].quantity == 2
    assert rows[2].scryfall_id is None
