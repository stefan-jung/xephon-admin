"""admin foundation: services and audit_log tables

Revision ID: 0001
Revises:
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("slug", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(255), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("roles", JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("actor_subject", sa.String(128), nullable=False),
        sa.Column("actor_email", sa.String(255), nullable=False, server_default=""),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("target_user_id", sa.String(128), nullable=True),
        sa.Column("target_user_email", sa.String(255), nullable=True),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_log_actor_subject", "audit_log", ["actor_subject"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_target_user_id", "audit_log", ["target_user_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # Seed initial services
    op.execute("""
        INSERT INTO services (slug, name, base_url, enabled, roles) VALUES
        ('xephon-cms',  'Xephon CMS',  'http://localhost:8000', true, '[]'),
        ('xephon-pm',   'Xephon PM',   'http://localhost:8001', true, '["xephon:pm-member","xephon:pm-admin"]'),
        ('xephon-pim',  'Xephon PIM',  'http://localhost:8002', true, '["xephon:pim-viewer","xephon:pim-editor"]'),
        ('xephon-erp',  'Xephon ERP',  'http://localhost:8003', true, '["erp:accountant","erp:admin"]'),
        ('xephon-admin','Xephon Admin','http://localhost:8004', true, '["xephon:admin"]')
    """)


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", "audit_log")
    op.drop_index("ix_audit_log_target_user_id", "audit_log")
    op.drop_index("ix_audit_log_action", "audit_log")
    op.drop_index("ix_audit_log_actor_subject", "audit_log")
    op.drop_table("audit_log")
    op.drop_table("services")
