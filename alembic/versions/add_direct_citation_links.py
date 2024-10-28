"""Add direct citation linking

Revision ID: add_direct_citation_links
Revises: f9a6638d6233
Create Date: 2024-03-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_direct_citation_links'
down_revision: Union[str, None] = 'f9a6638d6233'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # First add sentence_id to text_lines
    op.add_column('text_lines',
        sa.Column('sentence_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create unique constraint on sentence_id
    op.create_unique_constraint(
        'uq_text_lines_sentence_id',
        'text_lines',
        ['sentence_id']
    )
    
    # Create index for sentence_id on text_lines
    op.create_index(
        'ix_text_lines_sentence_id',
        'text_lines',
        ['sentence_id']
    )
    
    # Add sentence_id to lexical_values for direct linking
    op.add_column('lexical_values',
        sa.Column('sentence_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_lexical_values_sentence_id',
        'lexical_values', 'text_lines',
        ['sentence_id'], ['sentence_id']
    )
    
    # Create index for efficient lookups
    op.create_index(
        'ix_lexical_values_sentence_id',
        'lexical_values',
        ['sentence_id']
    )

def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint(
        'fk_lexical_values_sentence_id',
        'lexical_values',
        type_='foreignkey'
    )
    
    # Remove indexes
    op.drop_index('ix_lexical_values_sentence_id')
    op.drop_index('ix_text_lines_sentence_id')
    
    # Remove unique constraint
    op.drop_constraint(
        'uq_text_lines_sentence_id',
        'text_lines'
    )
    
    # Remove columns
    op.drop_column('lexical_values', 'sentence_id')
    op.drop_column('text_lines', 'sentence_id')
