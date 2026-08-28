"""Add durable AI conversations, messages, and answer runs.

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
        "ai_conversations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("profile_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("message_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
            "status IN ('active', 'archived', 'deleted')",
            name="ck_ai_conversations_status",
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["birth_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"])
    op.create_index("ix_ai_conversations_profile_id", "ai_conversations", ["profile_id"])
    op.create_index("ix_ai_conversations_status", "ai_conversations", ["status"])
    op.create_index(
        "ix_ai_conversations_user_last_message",
        "ai_conversations",
        ["user_id", "last_message_at"],
    )
    op.create_index(
        "ix_ai_conversations_user_profile_last_message",
        "ai_conversations",
        ["user_id", "profile_id", "last_message_at"],
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("turn_id", sa.String(36), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("structured_content", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_ai_messages_role"),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_ai_messages_status",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["ai_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "sequence_no",
            name="uq_ai_messages_conversation_sequence",
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "turn_id",
            "role",
            name="uq_ai_messages_conversation_turn_role",
        ),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])
    op.create_index("ix_ai_messages_turn_id", "ai_messages", ["turn_id"])
    op.create_index("ix_ai_messages_status", "ai_messages", ["status"])
    op.create_index(
        "ix_ai_messages_conversation_created",
        "ai_messages",
        ["conversation_id", "created_at"],
    )

    op.create_table(
        "ai_answer_runs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(16), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("degradation_reason", sa.String(64), nullable=True),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("chart_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("violation_codes", sa.JSON(), nullable=False),
        sa.Column("interpretation_receipt", sa.Text(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_ai_answer_runs_status",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["ai_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "idempotency_key",
            name="uq_ai_answer_runs_conversation_idempotency",
        ),
    )
    op.create_index("ix_ai_answer_runs_conversation_id", "ai_answer_runs", ["conversation_id"])
    op.create_index("ix_ai_answer_runs_status", "ai_answer_runs", ["status"])
    op.create_index(
        "ix_ai_answer_runs_chart_fingerprint",
        "ai_answer_runs",
        ["chart_fingerprint"],
    )
    op.create_index(
        "ix_ai_answer_runs_conversation_status",
        "ai_answer_runs",
        ["conversation_id", "status"],
    )


def downgrade():
    op.drop_table("ai_answer_runs")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
