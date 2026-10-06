"""add settings fields to user

Revision ID: add_settings_fields
Revises: a01560f063c9
Create Date: 2026-08-07 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_settings_fields'
down_revision: Union[str, Sequence[str], None] = 'a01560f063c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns as nullable first
    op.add_column('users', sa.Column('theme_preference', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('notification_preferences', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('two_factor_secret', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('last_password_change', sa.DateTime(timezone=True), nullable=True))

    # Update existing rows with default values
    op.execute("UPDATE users SET theme_preference = 'system' WHERE theme_preference IS NULL")
    op.execute("UPDATE users SET two_factor_enabled = 0 WHERE two_factor_enabled IS NULL")

    # Now make them NOT NULL
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('theme_preference', nullable=False)
        batch_op.alter_column('two_factor_enabled', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'theme_preference')
    op.drop_column('users', 'notification_preferences')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'two_factor_secret')
    op.drop_column('users', 'last_password_change')