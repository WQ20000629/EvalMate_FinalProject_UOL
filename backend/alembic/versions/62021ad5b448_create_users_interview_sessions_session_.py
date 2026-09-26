# ------------------------------------------------------------------
# File: backend/alembic/versions/62021ad5b448_create_users_interview_sessions_session_.py
# Purpose: Creates the users, interview_sessions, and session_answers tables.
# ------------------------------------------------------------------

"""create users, interview_sessions, session_answers

Revision ID: 62021ad5b448
Revises: 
Create Date: 2026-08-28 00:56:45.224291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62021ad5b448'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create each table, then the indexes used for lookups
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('interview_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('job_description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('final_overall_score', sa.Float(), nullable=False),
    sa.Column('avg_relevance', sa.Float(), nullable=False),
    sa.Column('avg_content_depth', sa.Float(), nullable=False),
    sa.Column('avg_clarity_structure', sa.Float(), nullable=False),
    sa.Column('avg_confidence_delivery', sa.Float(), nullable=False),
    sa.Column('avg_sentiment_score', sa.Float(), nullable=True),
    sa.Column('avg_eye_contact', sa.Float(), nullable=True),
    sa.Column('dominant_sentiment', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_sessions_id'), 'interview_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_user_id'), 'interview_sessions', ['user_id'], unique=False)
    op.create_table('session_answers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('question', sa.Text(), nullable=False),
    sa.Column('question_type', sa.String(), nullable=False),
    sa.Column('transcript', sa.Text(), nullable=False),
    sa.Column('relevance_score', sa.Float(), nullable=False),
    sa.Column('relevance_rationale', sa.Text(), nullable=False),
    sa.Column('content_depth_score', sa.Float(), nullable=False),
    sa.Column('content_depth_rationale', sa.Text(), nullable=False),
    sa.Column('clarity_structure_score', sa.Float(), nullable=False),
    sa.Column('clarity_structure_rationale', sa.Text(), nullable=False),
    sa.Column('confidence_delivery_score', sa.Float(), nullable=False),
    sa.Column('confidence_delivery_rationale', sa.Text(), nullable=False),
    sa.Column('sentiment_label', sa.String(), nullable=False),
    sa.Column('sentiment_confidence', sa.Float(), nullable=False),
    sa.Column('eye_contact_score', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_answers_id'), 'session_answers', ['id'], unique=False)
    op.create_index(op.f('ix_session_answers_session_id'), 'session_answers', ['session_id'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    # Drop the tables in reverse order so foreign keys are removed first
    op.drop_index(op.f('ix_session_answers_session_id'), table_name='session_answers')
    op.drop_index(op.f('ix_session_answers_id'), table_name='session_answers')
    op.drop_table('session_answers')
    op.drop_index(op.f('ix_interview_sessions_user_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_id'), table_name='interview_sessions')
    op.drop_table('interview_sessions')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')