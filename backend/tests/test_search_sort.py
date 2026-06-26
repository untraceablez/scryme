"""Sort-order tests: verify the `sort`/`descending` options and NULLs-last behavior."""

import uuid

import pytest
import pytest_asyncio
from src.models import Card
from src.scryfall.mapping import card_to_columns
from src.search import SearchScope
from src.search.engine import run_search

# Distinct mv/price/rarity/name, plus one card with no price to exercise NULLs-last.
_RAW = [
    {"id": str(uuid.uuid4()), "name": "Aaa Cheap", "set": "AAA", "collector_number": "1",
     "rarity": "common", "cmc": 1, "type_line": "Instant", "colors": [], "color_identity": [],
     "released_at": "2001-01-01", "prices": {"usd": "0.10"}},
    {"id": str(uuid.uuid4()), "name": "Bbb Mid", "set": "BBB", "collector_number": "2",
     "rarity": "rare", "cmc": 3, "type_line": "Sorcery", "colors": [], "color_identity": [],
     "released_at": "2010-06-15", "prices": {"usd": "5.00"}},
    {"id": str(uuid.uuid4()), "name": "Ccc Pricey", "set": "CCC", "collector_number": "3",
     "rarity": "mythic", "cmc": 7, "type_line": "Creature", "colors": [], "color_identity": [],
     "released_at": "2020-11-20", "prices": {"usd": "99.00"}},
    {"id": str(uuid.uuid4()), "name": "Ddd NoPrice", "set": "DDD", "collector_number": "4",
     "rarity": "uncommon", "cmc": 2, "type_line": "Enchantment", "colors": [], "color_identity": [],
     "released_at": "2005-03-09", "prices": {}},
]


@pytest_asyncio.fixture
async def seeded(session):
    for raw in _RAW:
        session.add(Card(**card_to_columns(raw)))
    await session.commit()
    return _RAW


async def _ordered(session, **kwargs):
    result = await run_search(session, "", scope=SearchScope.ALL, page_size=100, **kwargs)
    return [c.name for c in result.cards]


@pytest.mark.asyncio
async def test_sort_name_default_is_ascending(seeded, session):
    assert await _ordered(session) == ["Aaa Cheap", "Bbb Mid", "Ccc Pricey", "Ddd NoPrice"]


@pytest.mark.asyncio
async def test_sort_mana_value(seeded, session):
    assert await _ordered(session, sort="mv") == [
        "Aaa Cheap", "Ddd NoPrice", "Bbb Mid", "Ccc Pricey"]
    assert await _ordered(session, sort="mv", descending=True) == [
        "Ccc Pricey", "Bbb Mid", "Ddd NoPrice", "Aaa Cheap"]


@pytest.mark.asyncio
async def test_sort_price_puts_missing_last(seeded, session):
    # Ascending by price; the card with no USD price sorts last despite the direction.
    assert await _ordered(session, sort="price") == [
        "Aaa Cheap", "Bbb Mid", "Ccc Pricey", "Ddd NoPrice"]
    # Descending keeps the priceless card last too (NULLs-last regardless of direction).
    assert await _ordered(session, sort="price", descending=True) == [
        "Ccc Pricey", "Bbb Mid", "Aaa Cheap", "Ddd NoPrice"]


@pytest.mark.asyncio
async def test_sort_rarity_rank(seeded, session):
    # common < uncommon < rare < mythic
    assert await _ordered(session, sort="rarity") == [
        "Aaa Cheap", "Ddd NoPrice", "Bbb Mid", "Ccc Pricey"]


@pytest.mark.asyncio
async def test_sort_released(seeded, session):
    assert await _ordered(session, sort="released", descending=True) == [
        "Ccc Pricey", "Bbb Mid", "Ddd NoPrice", "Aaa Cheap"]


@pytest.mark.asyncio
async def test_unknown_sort_falls_back_to_name(seeded, session):
    assert await _ordered(session, sort="bogus") == await _ordered(session, sort="name")
