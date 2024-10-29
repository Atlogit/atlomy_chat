"""add text_line_id to sentences

Revision ID: add_text_line_id_to_sentences
Revises: create_sentences_table
Create Date: 2024-10-29 02:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_text_line_id_to_sentences'
down_revision = 'create_sentences_table'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add text_line_id column
    op.add_column('sentences',
        sa.Column('text_line_id', sa.Integer(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_sentences_text_line_id',
        'sentences', 'text_lines',
        ['text_line_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add index for better join performance
    op.create_index(
        'ix_sentences_text_line_id',
        'sentences',
        ['text_line_id']
    )

def downgrade() -> None:
    op.drop_index('ix_sentences_text_line_id')
    op.drop_constraint('fk_sentences_text_line_id', 'sentences', type_='foreignkey')
    op.drop_column('sentences', 'text_line_id')
