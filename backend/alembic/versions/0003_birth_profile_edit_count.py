"""Track whether a birth profile has actually been edited.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "birth_profiles",
        sa.Column(
            "edit_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    # The previous release populated last_edited_at during creation. Preserve
    # cooldown only for rows whose profile was subsequently updated.
    op.execute(
        sa.text(
            "UPDATE birth_profiles SET edit_count = 1 "
            "WHERE updated_at > created_at"
        )
    )


def downgrade():
    op.drop_column("birth_profiles", "edit_count")
