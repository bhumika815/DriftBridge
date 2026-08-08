"""Add profile fields

Revision ID: 76a24a57ad55
Revises: e588e21bade0
Create Date: 2026-08-08 17:31:39.630102

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision = "76a24a57ad55"
down_revision = "e588e21bade0"
branch_labels = None
depends_on = None


def upgrade():
    # Bio and interests were already added during the previous
    # migration attempt. We only need to add points now.

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "points",
                sa.Integer(),
                nullable=False,
                server_default="0"
            )
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("points")