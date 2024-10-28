"""Add sentence context fields to citations

Revision ID: add_sentence_context
Revises: merge_migration_branches
Create Date: 2024-03-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_sentence_context'
down_revision: Union[str, None] = 'merge_migration_branches'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add sentence_id to text_lines for direct sentence linking
    op.add_column('text_lines', sa.Column('sentence_id', 
        postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add index for efficient sentence lookups
    op.create_index(op.f('ix_text_lines_sentence_id'),
                   'text_lines', ['sentence_id'])

    # Add sentence context fields to lexical_values
    op.add_column('lexical_values', sa.Column('sentence_contexts',
        postgresql.JSONB(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    # Remove sentence context fields
    op.drop_column('lexical_values', 'sentence_contexts')
    op.drop_index(op.f('ix_text_lines_sentence_id'))
    op.drop_column('text_lines', 'sentence_id')
