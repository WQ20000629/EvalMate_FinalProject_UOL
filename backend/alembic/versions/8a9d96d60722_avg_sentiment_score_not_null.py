# ------------------------------------------------------------------
# File: backend/alembic/versions/8a9d96d60722_avg_sentiment_score_not_null.py
# Purpose: Makes avg_sentiment_score a required column on interview sessions.
# ------------------------------------------------------------------

"""avg_sentiment_score not null

Revision ID: 8a9d96d60722
Revises: f2dd83472a5c
Create Date: 2026-09-19 01:42:37.773789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a9d96d60722'
down_revision: Union[str, Sequence[str], None] = 'f2dd83472a5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Every saved session now has a sentiment score, so the column cannot be empty
    op.alter_column('interview_sessions', 'avg_sentiment_score',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False)

def downgrade() -> None:
    """Downgrade schema."""
    # Allow empty sentiment scores again
    op.alter_column('interview_sessions', 'avg_sentiment_score',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True)