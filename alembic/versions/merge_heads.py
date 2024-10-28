"""merge heads

Revision ID: merge_heads
Revises: merge_migration_branches, add_lexical_values_table
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = None
branch_labels = None
depends_on = ('merge_migration_branches', 'add_lexical_values_table')

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
