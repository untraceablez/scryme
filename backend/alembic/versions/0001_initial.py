"""initial schema: cards, collection_card, ingest_state

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pg_trgm powers fast ILIKE / regex (~) scans on name and oracle_text.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "cards",
        sa.Column("scryfall_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("oracle_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("set_code", sa.String(16), nullable=False),
        sa.Column("set_name", sa.String(256)),
        sa.Column("collector_number", sa.String(32), nullable=False),
        sa.Column("rarity", sa.String(32)),
        sa.Column("mana_cost", sa.String(128)),
        sa.Column("cmc", sa.Float()),
        sa.Column("type_line", sa.String(256)),
        sa.Column("oracle_text", sa.Text()),
        sa.Column("power", sa.String(16)),
        sa.Column("toughness", sa.String(16)),
        sa.Column("loyalty", sa.String(16)),
        sa.Column("colors", postgresql.ARRAY(sa.String(2))),
        sa.Column("color_identity", postgresql.ARRAY(sa.String(2))),
        sa.Column("keywords", postgresql.ARRAY(sa.String(64))),
        sa.Column("lang", sa.String(8), nullable=False, server_default="en"),
        sa.Column("layout", sa.String(32)),
        sa.Column("released_at", sa.Date()),
        sa.Column("legalities", postgresql.JSONB()),
        sa.Column("prices", postgresql.JSONB()),
        sa.Column("image_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("raw", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_cards_oracle_id", "cards", ["oracle_id"])
    op.create_index("ix_cards_name", "cards", ["name"])
    op.create_index("ix_cards_set_code", "cards", ["set_code"])
    op.create_index("ix_cards_rarity", "cards", ["rarity"])
    op.create_index("ix_cards_cmc", "cards", ["cmc"])
    op.create_index("ix_cards_lang", "cards", ["lang"])
    op.create_index("ix_cards_released_at", "cards", ["released_at"])
    op.create_index("ix_cards_set_collector", "cards", ["set_code", "collector_number"])
    op.create_index("ix_cards_colors_gin", "cards", ["colors"], postgresql_using="gin")
    op.create_index(
        "ix_cards_color_identity_gin", "cards", ["color_identity"], postgresql_using="gin"
    )
    op.create_index("ix_cards_keywords_gin", "cards", ["keywords"], postgresql_using="gin")
    op.create_index("ix_cards_raw_gin", "cards", ["raw"], postgresql_using="gin")
    op.execute(
        "CREATE INDEX ix_cards_name_trgm ON cards USING gin (name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_cards_oracle_text_trgm ON cards USING gin (oracle_text gin_trgm_ops)"
    )

    op.create_table(
        "collection_card",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "scryfall_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cards.scryfall_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("finish", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("condition", sa.String(32)),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("purchase_price", sa.Float()),
        sa.Column("binder_name", sa.String(256)),
        sa.Column("source_format", sa.String(32)),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "scryfall_id",
            "finish",
            "condition",
            "language",
            "binder_name",
            name="uq_collection_stack",
        ),
    )
    op.create_index("ix_collection_card_scryfall_id", "collection_card", ["scryfall_id"])

    op.create_table(
        "ingest_state",
        sa.Column("bulk_type", sa.String(32), primary_key=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column("last_downloaded_at", sa.DateTime(timezone=True)),
        sa.Column("card_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="idle"),
    )


def downgrade() -> None:
    op.drop_table("ingest_state")
    op.drop_table("collection_card")
    op.drop_table("cards")
