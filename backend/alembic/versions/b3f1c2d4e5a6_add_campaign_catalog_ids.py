"""add campaign catalog ids

Revision ID: b3f1c2d4e5a6
Revises: 642ba2c91703
Create Date: 2026-11-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f1c2d4e5a6'
down_revision: Union[str, Sequence[str], None] = 'c814701113a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'campaigns',
        sa.Column('domain_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'campaigns',
        sa.Column('group_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'campaigns',
        sa.Column('traffic_source_id', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('campaigns', 'traffic_source_id')
    op.drop_column('campaigns', 'group_id')
    op.drop_column('campaigns', 'domain_id')
