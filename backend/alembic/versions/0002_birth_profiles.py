"""Add user-owned birth profiles and deterministic chart snapshots.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "birth_profiles",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gender", sa.String(8), nullable=False),
        sa.Column("calendar_type", sa.String(8), nullable=False),
        sa.Column("birth_date", sa.String(10), nullable=False),
        sa.Column("solar_birth_date", sa.Date(), nullable=False),
        sa.Column("birth_hour", sa.Integer(), nullable=True),
        sa.Column("birth_minute", sa.Integer(), nullable=True),
        sa.Column("birth_place", sa.String(200), nullable=False),
        sa.Column("is_leap_month", sa.Boolean(), nullable=False),
        sa.Column("time_label", sa.String(40), nullable=False),
        sa.Column("last_edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("gender IN ('男', '女')", name="ck_birth_profiles_gender"),
        sa.CheckConstraint(
            "calendar_type IN ('solar', 'lunar')",
            name="ck_birth_profiles_calendar_type",
        ),
        sa.CheckConstraint(
            "(birth_hour IS NULL AND birth_minute IS NULL) OR "
            "(birth_hour BETWEEN 0 AND 23 AND birth_minute BETWEEN 0 AND 59)",
            name="ck_birth_profiles_time_pair",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_birth_profiles_user_id", "birth_profiles", ["user_id"], unique=False)

    op.create_table(
        "bazi_charts",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("profile_id", sa.String(36), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("chart_fingerprint", sa.String(64), nullable=False),
        sa.Column("engine_version", sa.String(32), nullable=False),
        sa.Column("chart_json", sa.JSON(), nullable=False),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["birth_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id"),
    )
    op.create_index(
        "ix_bazi_charts_chart_fingerprint",
        "bazi_charts",
        ["chart_fingerprint"],
        unique=False,
    )


def downgrade():
    op.drop_table("bazi_charts")
    op.drop_table("birth_profiles")
