"""Add sentence_contexts to lexical_values

Revision ID: add_sentence_contexts
Revises: 4b4e34b4f167
Create Date: 2024-10-29 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'add_sentence_contexts'
down_revision = '4b4e34b4f167'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add sentence_contexts column to lexical_values
    op.add_column('lexical_values',
        sa.Column('sentence_contexts', JSONB, nullable=True),
        schema=None
    )

def downgrade() -> None:
    # Remove sentence_contexts column
    op.drop_column('lexical_values', 'sentence_contexts')
