"""add connector_types to stations

Revision ID: 2137c9c78eef
Revises: 950aa0510a33
Create Date: 2026-09-10 12:13:14.018069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2137c9c78eef'
down_revision: Union[str, None] = '950aa0510a33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default='{}' so existing rows (already populated by earlier
    # ETL runs) get a valid empty array instead of failing the NOT NULL
    # constraint; dropped afterward since new rows always provide a value
    # explicitly via the ORM/upsert logic.
    op.add_column(
        "stations",
        sa.Column(
            "connector_types",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.alter_column("stations", "connector_types", server_default=None)
    # Note: op.drop_index('idx_stations_geog', ...) intentionally omitted —
    # same known autogenerate false-positive as prior migrations (raw-SQL
    # created index, invisible to ORM metadata comparison).


def downgrade() -> None:
    op.drop_column("stations", "connector_types")
