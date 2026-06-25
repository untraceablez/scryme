"""Integration tests: query string -> SQL -> results against a seeded card set."""

import uuid

import pytest
import pytest_asyncio
from src.models import Card, CollectionCard
from src.scryfall.mapping import card_to_columns
from src.search import SearchError, SearchScope
from src.search.engine import run_search

# Minimal but diverse card set covering colors, types, rarity, mv, p/t, keywords, sets, prices.
_RAW = [
    {"id": str(uuid.uuid4()), "name": "Black Lotus", "set": "LEA", "collector_number": "232",
     "rarity": "rare", "cmc": 0, "type_line": "Artifact", "colors": [], "color_identity": [],
     "oracle_text": "Add three mana of any one color.", "released_at": "1993-08-05",
     "prices": {"usd": "9999.99"}, "legalities": {"vintage": "restricted"}},
    {"id": str(uuid.uuid4()), "name": "Lightning Bolt", "set": "MH2", "collector_number": "122",
     "rarity": "uncommon", "cmc": 1, "type_line": "Instant", "colors": ["R"],
     "color_identity": ["R"], "oracle_text": "Lightning Bolt deals 3 damage to any target.",
     "released_at": "2021-06-18", "prices": {"usd": "2.50"},
     "legalities": {"modern": "legal", "commander": "legal"}},
    {"id": str(uuid.uuid4()), "name": "Llanowar Elves", "set": "M19", "collector_number": "314",
     "rarity": "common", "cmc": 1, "type_line": "Creature — Elf Druid", "colors": ["G"],
     "color_identity": ["G"], "power": "1", "toughness": "1", "keywords": [],
     "oracle_text": "{T}: Add {G}.", "released_at": "2018-07-13", "prices": {"usd": "0.20"}},
    {"id": str(uuid.uuid4()), "name": "Niv-Mizzet, Parun", "set": "GRN",
     "collector_number": "192", "rarity": "mythic", "cmc": 6,
     "type_line": "Legendary Creature — Dragon Wizard",
     "colors": ["U", "R"], "color_identity": ["U", "R"], "power": "5", "toughness": "5",
     "keywords": ["Flying"], "oracle_text": "Whenever a player draws a card...",
     "released_at": "2018-10-05", "prices": {"usd": "5.00"},
     "legalities": {"modern": "legal", "commander": "legal"}},
    {"id": str(uuid.uuid4()), "name": "Goblin Guide", "set": "ZEN", "collector_number": "145",
     "rarity": "rare", "cmc": 1, "type_line": "Creature — Goblin Scout", "colors": ["R"],
     "color_identity": ["R"], "power": "2", "toughness": "2", "keywords": ["Haste"],
     "oracle_text": "Haste. Whenever Goblin Guide attacks...", "released_at": "2010-04-23",
     "prices": {"usd": "8.00"}, "legalities": {"modern": "legal"}},
    {"id": str(uuid.uuid4()), "name": "Island", "set": "MH2", "collector_number": "492",
     "rarity": "common", "cmc": 0, "type_line": "Basic Land — Island", "colors": [],
     "color_identity": ["U"], "oracle_text": "({T}: Add {U}.)", "released_at": "2021-06-18",
     "prices": {"usd": "0.10"}},
]


@pytest_asyncio.fixture
async def seeded(session):
    for raw in _RAW:
        session.add(Card(**card_to_columns(raw)))
    await session.commit()
    return _RAW


async def _names(session, query, scope=SearchScope.ALL):
    result = await run_search(session, query, scope=scope, page_size=100)
    return {c.name for c in result.cards}


@pytest.mark.asyncio
async def test_bare_name_substring(seeded, session):
    assert await _names(session, "goblin") == {"Goblin Guide"}


@pytest.mark.asyncio
async def test_color_contains_and_exact(seeded, session):
    assert await _names(session, "c:r") == {"Lightning Bolt", "Niv-Mizzet, Parun", "Goblin Guide"}
    assert await _names(session, "c=ur") == {"Niv-Mizzet, Parun"}
    assert await _names(session, "c:c") == {"Black Lotus", "Island"}  # colorless
    assert "Niv-Mizzet, Parun" in await _names(session, "c:m")  # multicolor


@pytest.mark.asyncio
async def test_identity(seeded, session):
    # Island is colorless-faced but blue identity.
    assert "Island" in await _names(session, "id:u")


@pytest.mark.asyncio
async def test_type_and_negation(seeded, session):
    assert await _names(session, "t:instant") == {"Lightning Bolt"}
    assert "Lightning Bolt" not in await _names(session, "-t:instant")


@pytest.mark.asyncio
async def test_mana_value_comparisons(seeded, session):
    assert await _names(session, "mv>=6") == {"Niv-Mizzet, Parun"}
    assert await _names(session, "cmc=0") == {"Black Lotus", "Island"}


@pytest.mark.asyncio
async def test_power_toughness(seeded, session):
    assert await _names(session, "pow>=5") == {"Niv-Mizzet, Parun"}
    assert await _names(session, "tou<=1") == {"Llanowar Elves"}


@pytest.mark.asyncio
async def test_rarity_ordering(seeded, session):
    assert await _names(session, "r:mythic") == {"Niv-Mizzet, Parun"}
    # >=rare includes rare + mythic
    assert await _names(session, "r>=rare") == {"Black Lotus", "Niv-Mizzet, Parun", "Goblin Guide"}


@pytest.mark.asyncio
async def test_set_and_keyword(seeded, session):
    assert await _names(session, "s:mh2") == {"Lightning Bolt", "Island"}
    assert await _names(session, "kw:flying") == {"Niv-Mizzet, Parun"}


@pytest.mark.asyncio
async def test_price_and_format(seeded, session):
    assert await _names(session, "usd>=8") == {"Black Lotus", "Goblin Guide"}
    assert await _names(session, "f:modern") == {
        "Lightning Bolt", "Niv-Mizzet, Parun", "Goblin Guide"}


@pytest.mark.asyncio
async def test_year(seeded, session):
    assert await _names(session, "year<=2011") == {"Black Lotus", "Goblin Guide"}


@pytest.mark.asyncio
async def test_regex_name_and_oracle(seeded, session):
    assert await _names(session, "/^Goblin/") == {"Goblin Guide"}
    assert "Niv-Mizzet, Parun" in await _names(session, "o:/draws a card/")


@pytest.mark.asyncio
async def test_boolean_combination(seeded, session):
    assert await _names(session, "c:r t:creature mv<=1") == {"Goblin Guide"}
    assert await _names(session, "t:instant OR t:artifact") == {"Lightning Bolt", "Black Lotus"}


@pytest.mark.asyncio
async def test_collection_scope_and_quantities(seeded, session):
    found = await run_search(session, "Lightning Bolt", scope=SearchScope.ALL)
    bolt = found.cards[0]
    session.add(CollectionCard(scryfall_id=bolt.scryfall_id, quantity=3))
    await session.commit()

    # Default scope only returns owned cards.
    result = await run_search(session, "", scope=SearchScope.COLLECTION)
    assert {c.name for c in result.cards} == {"Lightning Bolt"}
    assert result.quantities[str(bolt.scryfall_id)] == 3


@pytest.mark.asyncio
async def test_pagination(seeded, session):
    result = await run_search(session, "", scope=SearchScope.ALL, page=1, page_size=2)
    assert len(result.cards) == 2
    assert result.total == len(_RAW)
    assert result.total_pages == 3


@pytest.mark.asyncio
async def test_bad_number_raises(seeded, session):
    with pytest.raises(SearchError):
        await run_search(session, "mv>=abc", scope=SearchScope.ALL)
