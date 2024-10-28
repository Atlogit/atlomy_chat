"""merge migration branches

Revision ID: merge_migration_branches
Revises: add_lexical_values_table, fdff7b902322
Create Date: 2024-03-21 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_migration_branches'
down_revision = None
branch_labels = None
depends_on = ('add_lexical_values_table', 'fdff7b902322')

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
