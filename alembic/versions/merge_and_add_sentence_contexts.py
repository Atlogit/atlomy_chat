"""merge heads and add sentence_contexts

Revision ID: merge_and_add_sentence_contexts
Revises: add_direct_citation_links, add_author_work_names, merge_all_current_heads, add_lexical_values_table, merge_heads
Create Date: 2024-10-29 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'merge_and_add_sentence_contexts'
down_revision = None
branch_labels = None
depends_on = ['add_direct_citation_links', 'add_author_work_names', 'merge_all_current_heads', 'add_lexical_values_table', 'merge_heads']

def upgrade() -> None:
    # Add sentence_contexts column to lexical_values
    op.add_column('lexical_values',
        sa.Column('sentence_contexts', JSONB, nullable=True)
    )

def downgrade() -> None:
    # Remove sentence_contexts column
    op.drop_column('lexical_values', 'sentence_contexts')
