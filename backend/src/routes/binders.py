"""Binder browsing: view the owned collection grouped by its `binder_name`.

Binder names come from imports (e.g. ManaBox "Binder Name"); cards with no binder are grouped
under "Unsorted" (sentinel ``__none__``).
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models import Card, CollectionCard
from src.scryfall.images import ImageCache
from src.scryfall.mapping import image_url as cdn_image_url
from src.templating import templates

router = APIRouter(tags=["binders"])
_cache = ImageCache()

NONE_SENTINEL = "__none__"


def _image(card: Card) -> str:
    sid = str(card.scryfall_id)
    return _cache.url_path(sid) if _cache.is_cached(sid) else (cdn_image_url(card.raw) or "")


@dataclass
class CardView:
    card: Card
    quantity: int
    image: str


@router.get("/binders")
async def list_binders() -> RedirectResponse:
    # The binder index is now the Binders tab of /collection.
    return RedirectResponse(url="/collection?tab=binders", status_code=307)


@router.get("/binders/cards", response_class=HTMLResponse)
async def binder_cards(
    request: Request, name: str = "", session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    is_none = name == NONE_SENTINEL or name == ""
    condition = CollectionCard.binder_name.is_(None) if is_none else (
        CollectionCard.binder_name == name
    )
    rows = (
        await session.execute(
            select(Card, func.sum(CollectionCard.quantity))
            .join(CollectionCard, CollectionCard.scryfall_id == Card.scryfall_id)
            .where(condition)
            .group_by(Card)
            .order_by(Card.name)
        )
    ).all()
    views = [CardView(card=c, quantity=int(q), image=_image(c)) for c, q in rows]
    return templates.TemplateResponse(
        request,
        "binder_detail.html",
        {"views": views, "label": "Unsorted" if is_none else name},
    )
