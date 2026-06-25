import pytest


@pytest.mark.asyncio
async def test_home_empty_shows_upload(client):
    """With no collection, the home page prompts for an upload."""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "Upload a collection" in resp.text


@pytest.mark.asyncio
async def test_home_with_collection_shows_search(client, session):
    """Once a card is owned, the home page shows the search bar instead."""
    import uuid

    from src.models import Card, CollectionCard

    card = Card(
        scryfall_id=uuid.uuid4(),
        name="Black Lotus",
        set_code="lea",
        collector_number="232",
        raw={"name": "Black Lotus"},
    )
    session.add(card)
    await session.flush()
    session.add(CollectionCard(scryfall_id=card.scryfall_id, quantity=1))
    await session.commit()

    resp = await client.get("/")
    assert resp.status_code == 200
    assert 'name="q"' in resp.text
