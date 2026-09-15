"""Add missing user profile columns

Revision ID: a1b2c3d4e5f6
Revises: 6e0c900425cc
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6e0c900425cc'
branch_labels = None
depends_on = None


def upgrade():
    # Bio and interests already exist in the users table
    # from the earlier profile-fields migration.
    # Only is_admin is missing.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_admin',
                sa.Boolean(),
                nullable=False,
                server_default='0'
            )
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')