"""add geography index for radius search

Revision ID: 5a30dbbebfa7
Revises: 266b19746398
Create Date: 2026-09-10 10:39:25.473830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a30dbbebfa7'
down_revision: Union[str, None] = '266b19746398'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Radius search (SRS Mode B) queries use ST_DWithin against
    # geom::geography for accurate meter-based distances. The existing
    # idx_stations_geom GIST index is on the geometry type and is NOT used
    # by the planner for geography-cast queries (verified via EXPLAIN:
    # without this index, the query does a near-full index scan on an
    # unrelated column, ~77ms for 35k rows; with it, ~7.7ms via a proper
    # bitmap index scan). This expression index closes that gap.
    op.execute(
        "CREATE INDEX idx_stations_geog ON stations USING GIST ((geom::geography))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_stations_geog")
