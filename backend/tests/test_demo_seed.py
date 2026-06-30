"""Curated demo seed (#larger-demo): colour/price selection, banned/restricted, 2019 dating."""

import uuid

import pytest
from sqlalchemy import func, select
from src.demo import seed_demo
from src.models import Card, CardPricePoint, CollectionCard, PriceSnapshot


async def _card(session, *, colors, usd, legalities=None):
    card = Card(
        scryfall_id=uuid.uuid4(),
        oracle_id=uuid.uuid4(),
        name=f"Demo {uuid.uuid4().hex[:6]}",
        set_code="tst",
        collector_number="1",
        colors=colors,
        color_identity=colors,
        prices={"usd": usd} if usd else {},
        legalities=legalities or {},
        raw={"name": "Demo"},
    )
    session.add(card)
    await session.flush()
    return card


@pytest.mark.asyncio
async def test_curated_demo_seed(session):
    red_hi = await _card(session, colors=["R"], usd="9.00")
    red_lo = await _card(session, colors=["R"], usd="2.00")
    await _card(session, colors=["U"], usd="7.50")
    await _card(session, colors=[], usd="20.00")          # colorless
    await _card(session, colors=["R", "G"], usd="3.00")   # multicolor
    banned = await _card(session, colors=["B"], usd="40.00", legalities={"modern": "banned"})
    restricted = await _card(session, colors=["U"], usd="3000.00",
                             legalities={"vintage": "restricted"})
    await session.commit()

    added = await seed_demo()
    assert added >= 7

    owned = set(await session.scalars(select(CollectionCard.scryfall_id)))
    assert {red_hi.scryfall_id, red_lo.scryfall_id, banned.scryfall_id,
            restricted.scryfall_id} <= owned

    rows = list((await session.execute(select(CollectionCard))).scalars())
    assert all(r.source_format == "demo" for r in rows)
    assert all(r.added_at.year == 2019 for r in rows)
    assert any(r.purchase_price for r in rows)  # priced cards get an acquisition price

    # Synthesized price history for the value chart + movers points for the read-only demo.
    assert (await session.scalar(select(func.count()).select_from(PriceSnapshot))) > 12
    assert (await session.scalar(select(func.count()).select_from(CardPricePoint))) > 0


@pytest.mark.asyncio
async def test_seed_is_idempotent(session):
    await _card(session, colors=["R"], usd="6.00")
    await session.commit()
    assert await seed_demo() >= 1
    # A second run re-evaluates (the tiny collection is under the skip guard) but must not
    # re-add cards it already owns.
    before = await session.scalar(select(func.count()).select_from(CollectionCard))
    await seed_demo()
    after = await session.scalar(select(func.count()).select_from(CollectionCard))
    assert after == before
