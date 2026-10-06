"""add similar_ticket_ids to tickets

Revision ID: add_similar_ticket_ids
Revises: add_settings_fields
Create Date: 2026-08-10 04:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_similar_ticket_ids'
down_revision: Union[str, Sequence[str], None] = 'add_settings_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('similar_ticket_ids', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'similar_ticket_ids')
