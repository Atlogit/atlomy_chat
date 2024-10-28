"""Add author and work name fields to text_divisions

Revision ID: add_author_work_names
Revises: merge_migration_branches
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_author_work_names'
down_revision = 'merge_migration_branches'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add columns for author and work names
    op.add_column('text_divisions', sa.Column('author_name', sa.String(), nullable=True))
    op.add_column('text_divisions', sa.Column('work_name', sa.String(), nullable=True))
    
    # Create index for efficient lookups
    op.create_index('ix_text_divisions_author_work_names', 'text_divisions', ['author_name', 'work_name'])

def downgrade() -> None:
    # Remove the added columns and index
    op.drop_index('ix_text_divisions_author_work_names', table_name='text_divisions')
    op.drop_column('text_divisions', 'work_name')
    op.drop_column('text_divisions', 'author_name')
