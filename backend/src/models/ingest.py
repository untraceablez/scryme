"""The `ingest_state` table: tracks Scryfall bulk-data ingestion.

A single row (one per bulk `type`, e.g. ``default_cards``) records the last download so the
scheduler can honor Scryfall's "cache data for at least 24 hours" guidance.
"""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class IngestState(Base):
    __tablename__ = "ingest_state"

    bulk_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    # `updated_at` reported by Scryfall for the bulk file we last ingested.
    source_updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    last_downloaded_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    card_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="idle")  # idle | running | error
