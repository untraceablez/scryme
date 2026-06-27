"""Price history tests: snapshotting, value series, movers, and the route."""

import uuid

import pytest
from src.models import Card, CollectionCard
from src.prices import biggest_movers, collection_pl, snapshot_prices, value_series
from src.scryfall.mapping import card_to_columns


async def _seed(session):
    a = {"id": str(uuid.uuid4()), "oracle_id": str(uuid.uuid4()), "name": "Aaa", "set": "TST",
         "collector_number": "1", "rarity": "common", "cmc": 1, "type_line": "Creature",
         "colors": ["W"], "color_identity": ["W"], "prices": {"usd": "1.00"}}
    b = {"id": str(uuid.uuid4()), "oracle_id": str(uuid.uuid4()), "name": "Bbb", "set": "TST",
         "collector_number": "2", "rarity": "rare", "cmc": 3, "type_line": "Instant",
         "colors": ["U"], "color_identity": ["U"], "prices": {"usd": "5.00", "usd_foil": "12.00"}}
    ca, cb = Card(**card_to_columns(a)), Card(**card_to_columns(b))
    session.add_all([ca, cb])
    await session.flush()
    session.add(CollectionCard(scryfall_id=ca.scryfall_id, quantity=2, finish="normal"))
    session.add(CollectionCard(scryfall_id=cb.scryfall_id, quantity=1, finish="foil"))
    await session.commit()
    return ca, cb


@pytest.mark.asyncio
async def test_snapshot_value_is_foil_aware(session):
    await _seed(session)
    snap = await snapshot_prices(session)
    # 2 * 1.00 (normal) + 1 * 12.00 (foil) = 14.00
    assert snap.total_usd == 14.00
    assert snap.card_count == 2  # both have a market USD


@pytest.mark.asyncio
async def test_empty_collection_snapshot_is_none(session):
    assert await snapshot_prices(session) is None


@pytest.mark.asyncio
async def test_value_series_is_chronological(session):
    await _seed(session)
    await snapshot_prices(session)
    await snapshot_prices(session)
    series = await value_series(session)
    assert len(series) == 2
    assert series[0].captured_at <= series[1].captured_at


@pytest.mark.asyncio
async def test_biggest_movers(session):
    ca, _ = await _seed(session)
    await snapshot_prices(session)
    # Aaa's market price rises 1.00 -> 3.00; re-snapshot.
    ca.raw = {**ca.raw, "prices": {"usd": "3.00"}}
    ca.prices = {"usd": "3.00"}
    await session.commit()
    await snapshot_prices(session)

    movers = await biggest_movers(session)
    assert movers.available
    assert [m.name for m in movers.gainers] == ["Aaa"]
    top = movers.gainers[0]
    assert top.old == 1.00 and top.new == 3.00 and top.delta == 2.00 and top.pct == 200.0
    assert movers.losers == []


async def _seed_pl(session):
    """A winner (A), a loser (B, foil), and an unpriced stack (C, no purchase price)."""
    a = {"id": str(uuid.uuid4()), "oracle_id": str(uuid.uuid4()), "name": "Aaa", "set": "TST",
         "collector_number": "1", "rarity": "common", "prices": {"usd": "1.00"}}
    b = {"id": str(uuid.uuid4()), "oracle_id": str(uuid.uuid4()), "name": "Bbb", "set": "TST",
         "collector_number": "2", "rarity": "rare", "prices": {"usd": "5.00", "usd_foil": "12.00"}}
    c = {"id": str(uuid.uuid4()), "oracle_id": str(uuid.uuid4()), "name": "Ccc", "set": "TST",
         "collector_number": "3", "rarity": "common", "prices": {"usd": "2.00"}}
    ca, cb, cc = (Card(**card_to_columns(x)) for x in (a, b, c))
    session.add_all([ca, cb, cc])
    await session.flush()
    session.add(CollectionCard(scryfall_id=ca.scryfall_id, quantity=2, finish="normal",
                               purchase_price=0.50))
    session.add(CollectionCard(scryfall_id=cb.scryfall_id, quantity=1, finish="foil",
                               purchase_price=20.00))
    session.add(CollectionCard(scryfall_id=cc.scryfall_id, quantity=1, finish="normal"))
    await session.commit()


@pytest.mark.asyncio
async def test_collection_pl_totals_and_movers(session):
    await _seed_pl(session)
    pl = await collection_pl(session)
    assert pl.available
    # cost: 2*0.50 + 1*20.00 = 21.00 ; market (foil-aware): 2*1.00 + 1*12.00 = 14.00
    assert pl.cost_basis == 21.00
    assert pl.market_value == 14.00
    assert pl.unrealized == -7.00
    assert pl.pct == -33.3
    assert pl.priced_stacks == 2
    assert pl.priced_cards == 3
    assert pl.unpriced_stacks == 1  # Ccc has no purchase price
    assert [w.name for w in pl.winners] == ["Aaa"]
    assert pl.winners[0].total_delta == 1.00  # 2 * (1.00 - 0.50)
    assert [loser.name for loser in pl.losers] == ["Bbb"]
    assert pl.losers[0].total_delta == -8.00  # 1 * (12.00 - 20.00), foil price


@pytest.mark.asyncio
async def test_collection_pl_empty_when_no_purchase_prices(session):
    await _seed(session)  # _seed sets no purchase prices
    pl = await collection_pl(session)
    assert not pl.available
    assert pl.cost_basis == 0.0
    assert pl.unpriced_stacks == 2


@pytest.mark.asyncio
async def test_prices_route_renders(client, session):
    await _seed(session)
    await snapshot_prices(session)
    resp = await client.get("/prices")
    assert resp.status_code == 200
    assert "Collection value" in resp.text
    assert "$14.00" in resp.text


@pytest.mark.asyncio
async def test_prices_route_shows_pl(client, session):
    await _seed_pl(session)
    resp = await client.get("/prices")
    assert resp.status_code == 200
    assert "Acquisition P/L" in resp.text
    assert "Cost basis" in resp.text
