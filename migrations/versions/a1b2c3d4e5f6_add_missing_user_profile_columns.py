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
    # The User model declares bio and interests, but no migration ever
    # created those columns. Add them now as nullable so existing rows
    # are unaffected. Also add is_admin for the moderation module.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('interests', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')
        batch_op.drop_column('interests')
        batch_op.drop_column('bio')
