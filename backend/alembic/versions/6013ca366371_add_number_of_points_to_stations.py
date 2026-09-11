"""add number_of_points to stations

Revision ID: 6013ca366371
Revises: 2137c9c78eef
Create Date: 2026-09-10 12:32:01.254795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6013ca366371'
down_revision: Union[str, None] = '2137c9c78eef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stations', sa.Column('number_of_points', sa.Integer(), nullable=True))
    # Note: op.drop_index('idx_stations_geog', ...) intentionally omitted —
    # same known autogenerate false-positive as prior migrations.


def downgrade() -> None:
    op.drop_column('stations', 'number_of_points')
