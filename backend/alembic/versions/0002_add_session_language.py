"""add session language

Revision ID: 0002_add_session_language
Revises: 0001_initial_schema
Create Date: 2026-04-18 10:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_session_language"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column("language", sa.String(), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("interview_sessions", "language")