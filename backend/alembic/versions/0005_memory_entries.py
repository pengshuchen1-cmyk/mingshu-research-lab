"""Add account-scoped memory archive entries.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "memory_entries",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(50), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("is_timeline_event", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("source", sa.String(16), server_default="manual", nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("ai_use_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('基本信息', '职业事业', '感情关系', '家庭生活', "
            "'健康状态', '目标愿望', '重要人物', '其他记忆')",
            name="ck_memory_entries_category",
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'ai')",
            name="ck_memory_entries_source",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_memory_entries_category", "memory_entries", ["category"], unique=False
    )
    op.create_index(
        "ix_memory_entries_occurred_on", "memory_entries", ["occurred_on"], unique=False
    )
    op.create_index(
        "ix_memory_entries_user_id", "memory_entries", ["user_id"], unique=False
    )


def downgrade():
    op.drop_table("memory_entries")
