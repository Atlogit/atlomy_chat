"""create sentences table

Revision ID: create_sentences_table
Revises: merge_and_add_sentence_contexts
Create Date: 2024-10-29 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON

# revision identifiers, used by Alembic.
revision = 'create_sentences_table'
down_revision = 'merge_and_add_sentence_contexts'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('sentences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('source_line_ids', ARRAY(sa.Integer()), nullable=False),
        sa.Column('start_position', sa.Integer(), nullable=False),
        sa.Column('end_position', sa.Integer(), nullable=False),
        sa.Column('spacy_data', JSON(), nullable=True),
        sa.Column('categories', ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index on content for faster searches
    op.create_index(op.f('ix_sentences_content'), 'sentences', ['content'])

def downgrade() -> None:
    op.drop_index(op.f('ix_sentences_content'), table_name='sentences')
    op.drop_table('sentences')
