"""Add lexical values table

Revision ID: add_lexical_values_table
Revises: f9a6638d6233
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

# revision identifiers, used by Alembic.
revision = 'add_lexical_values_table'
down_revision = 'f9a6638d6233'  # Updated to use the UUID migration as parent
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'lexical_values',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('lemma', sa.String(), nullable=False),
        sa.Column('translation', sa.String()),
        sa.Column('short_description', sa.Text()),
        sa.Column('long_description', sa.Text()),
        sa.Column('related_terms', ARRAY(sa.String())),
        sa.Column('citations_used', JSONB),
        sa.Column('references', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        
        sa.UniqueConstraint('lemma', name='uq_lexical_values_lemma'),
        sa.Index('ix_lexical_values_lemma', 'lemma')
    )

def downgrade() -> None:
    op.drop_table('lexical_values')
