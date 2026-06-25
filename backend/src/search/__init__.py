"""Scryfall-compatible search engine.

Pipeline: ``lexer`` tokenizes the query, ``parser`` builds an AST of boolean operators and
filter terms, and ``compiler`` translates the AST into SQLAlchemy conditions over the ``cards``
table. ``engine.build_search`` assembles the final query, optionally scoped to the owned
collection.

The implemented filter set is a faithful subset of https://scryfall.com/docs/syntax; unknown
keywords raise :class:`~src.search.errors.SearchError` rather than failing silently.
"""

from src.search.engine import SearchScope, build_search
from src.search.errors import SearchError

__all__ = ["SearchError", "SearchScope", "build_search"]
