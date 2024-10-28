"""merge all current heads

Revision ID: merge_all_current_heads
Revises: merge_heads, add_lexical_values_table, add_author_work_names
Create Date: 2024-03-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_all_current_heads'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Update this to include all current effective heads
depends_on = ['merge_heads', 'add_lexical_values_table', 'add_author_work_names']

def upgrade() -> None:
    # Add sentence_id to text_lines for direct sentence linking
    op.add_column('text_lines', sa.Column('sentence_id', 
        sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add index for efficient sentence lookups
    op.create_index(op.f('ix_text_lines_sentence_id'),
                   'text_lines', ['sentence_id'])

    # Add sentence context fields to lexical_values
    op.add_column('lexical_values', sa.Column('sentence_contexts',
        sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    # Remove sentence context fields
    op.drop_column('lexical_values', 'sentence_contexts')
    op.drop_index(op.f('ix_text_lines_sentence_id'))
    op.drop_column('text_lines', 'sentence_id')
