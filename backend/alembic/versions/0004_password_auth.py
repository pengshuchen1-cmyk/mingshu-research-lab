"""Add password authentication state.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "auth_version",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_failed_attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column("password_locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("users", "password_locked_until")
    op.drop_column("users", "password_failed_attempts")
    op.drop_column("users", "auth_version")
    op.drop_column("users", "password_hash")
