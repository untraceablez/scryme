"""Search route tests: full page vs HTMX partial, scope, and error rendering."""

import uuid

import pytest
from src.models import Card, CollectionCard
from src.scryfall.mapping import card_to_columns


async def _seed_owned(session):
    raw = {"id": str(uuid.uuid4()), "name": "Lightning Bolt", "set": "MH2",
           "collector_number": "122", "rarity": "uncommon", "cmc": 1, "type_line": "Instant",
           "colors": ["R"], "color_identity": ["R"], "scryfall_uri": "https://scryfall.test/bolt",
           "oracle_text": "deals 3 damage", "prices": {"usd": "2.50"}}
    card = Card(**card_to_columns(raw))
    session.add(card)
    await session.flush()
    session.add(CollectionCard(scryfall_id=card.scryfall_id, quantity=2))
    await session.commit()
    return card


@pytest.mark.asyncio
async def test_full_page_render(client, session):
    await _seed_owned(session)
    resp = await client.get("/search", params={"q": "bolt"})
    assert resp.status_code == 200
    assert "<html" in resp.text  # full document
    assert "Lightning Bolt" in resp.text
    assert "×2" in resp.text  # owned quantity badge


@pytest.mark.asyncio
async def test_htmx_returns_partial(client, session):
    await _seed_owned(session)
    resp = await client.get("/search", params={"q": "bolt"}, headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "<html" not in resp.text  # partial only
    assert "Lightning Bolt" in resp.text


@pytest.mark.asyncio
async def test_invalid_query_shows_error(client):
    resp = await client.get("/search", params={"q": "bogus:value"}, headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "Unknown filter" in resp.text


@pytest.mark.asyncio
async def test_scope_all_searches_unowned(client, session):
    # Seed a card NOT in the collection; collection scope hides it, all scope finds it.
    raw = {"id": str(uuid.uuid4()), "name": "Black Lotus", "set": "LEA",
           "collector_number": "232", "rarity": "rare", "cmc": 0, "type_line": "Artifact",
           "colors": [], "color_identity": []}
    session.add(Card(**card_to_columns(raw)))
    await session.commit()

    owned = await client.get("/search", params={"q": "lotus", "scope": "collection"},
                             headers={"HX-Request": "true"})
    assert "Black Lotus" not in owned.text

    all_cards = await client.get("/search", params={"q": "lotus", "scope": "all"},
                                 headers={"HX-Request": "true"})
    assert "Black Lotus" in all_cards.text
