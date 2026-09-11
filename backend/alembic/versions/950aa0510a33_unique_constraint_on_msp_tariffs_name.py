"""unique constraint on msp_tariffs.name

Revision ID: 950aa0510a33
Revises: 5a30dbbebfa7
Create Date: 2026-09-10 11:00:42.592417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '950aa0510a33'
down_revision: Union[str, None] = '5a30dbbebfa7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_msp_tariffs_name'), 'msp_tariffs', ['name'], unique=True)
    # Note: op.drop_index('idx_stations_geog', ...) intentionally omitted —
    # autogenerate incorrectly flags this for removal because it was created
    # via raw SQL (migration 5a30dbbebfa7), not via the ORM model, so it's
    # invisible to SQLAlchemy metadata comparison. Keep it.


def downgrade() -> None:
    op.drop_index(op.f('ix_msp_tariffs_name'), table_name='msp_tariffs')
