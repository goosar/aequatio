# pylint: disable=import-error,no-member
"""Create users table

Revision ID: 0002
Revises: 0001
Create Date: 2025-10-18 10:00:00.000000

"""

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

from alembic import op  # type: ignore  # pylint: disable=import-error

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001_create_events_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table with indexes and constraints."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    """Drop users table and indexes."""
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
