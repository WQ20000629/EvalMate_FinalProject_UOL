# ------------------------------------------------------------------
# File: backend/alembic/versions/f2dd83472a5c_add_cascade_delete_to_session_foreign_.py
# Purpose: Deletes sessions and answers automatically when their parent row is deleted.
# ------------------------------------------------------------------

"""add cascade delete to session foreign keys

Revision ID: f2dd83472a5c
Revises: 62021ad5b448
Create Date: 2026-08-28 01:08:05.834935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2dd83472a5c'
down_revision: Union[str, Sequence[str], None] = '62021ad5b448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Replace each foreign key with one that deletes child rows automatically
    op.drop_constraint(op.f('interview_sessions_user_id_fkey'), 'interview_sessions', type_='foreignkey')
    op.create_foreign_key(None, 'interview_sessions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint(op.f('session_answers_session_id_fkey'), 'session_answers', type_='foreignkey')
    op.create_foreign_key(None, 'session_answers', 'interview_sessions', ['session_id'], ['id'], ondelete='CASCADE')

def downgrade() -> None:
    """Downgrade schema."""
    # Put back the original foreign keys without cascade delete
    op.drop_constraint(None, 'session_answers', type_='foreignkey')
    op.create_foreign_key(op.f('session_answers_session_id_fkey'), 'session_answers', 'interview_sessions', ['session_id'], ['id'])
    op.drop_constraint(None, 'interview_sessions', type_='foreignkey')
    op.create_foreign_key(op.f('interview_sessions_user_id_fkey'), 'interview_sessions', 'users', ['user_id'], ['id'])