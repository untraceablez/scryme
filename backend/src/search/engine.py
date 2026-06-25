"""High-level search: assemble and run a query from a Scryfall-style string.

Scope:
  * COLLECTION (default) restricts results to cards the user owns;
  * ALL searches the full local card database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Card, CollectionCard
from src.search.compiler import compile_node
from src.search.parser import parse

DEFAULT_PAGE_SIZE = 60


class SearchScope(str, Enum):
    COLLECTION = "collection"
    ALL = "all"


@dataclass
class SearchResult:
    cards: list[Card]
    total: int
    page: int
    page_size: int
    quantities: dict[str, int] = field(default_factory=dict)

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


def build_search(query: str, scope: SearchScope = SearchScope.COLLECTION) -> Select:
    """Build a SELECT over cards for ``query`` (raises SearchError on a bad query)."""
    node = parse(query)
    stmt = select(Card)
    if scope is SearchScope.COLLECTION:
        # IN-subquery (not a join) keeps one row per printing even with multiple owned stacks.
        stmt = stmt.where(Card.scryfall_id.in_(select(CollectionCard.scryfall_id)))
    if node is not None:
        stmt = stmt.where(compile_node(node))
    return stmt.order_by(Card.name, Card.released_at)


async def _owned_quantities(session: AsyncSession, ids: list) -> dict[str, int]:
    if not ids:
        return {}
    rows = await session.execute(
        select(CollectionCard.scryfall_id, func.sum(CollectionCard.quantity))
        .where(CollectionCard.scryfall_id.in_(ids))
        .group_by(CollectionCard.scryfall_id)
    )
    return {str(sid): int(qty) for sid, qty in rows.all()}


async def run_search(
    session: AsyncSession,
    query: str,
    *,
    scope: SearchScope = SearchScope.COLLECTION,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> SearchResult:
    """Execute a search and return the requested page plus owned quantities."""
    page = max(1, page)
    base = build_search(query, scope)

    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.execute(base.limit(page_size).offset((page - 1) * page_size))
    cards = list(rows.scalars().all())

    quantities = await _owned_quantities(session, [c.scryfall_id for c in cards])
    return SearchResult(
        cards=cards, total=total, page=page, page_size=page_size, quantities=quantities
    )
